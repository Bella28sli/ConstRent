from django.db import connection
from typing import List, Dict, Optional
from datetime import date, datetime
from decimal import Decimal
from django.forms import ValidationError
from django.db import transaction
from django.utils import timezone

class RentalService:
    @staticmethod
    def log_action(staff_id: int, action_type: str, description: str, success: bool = True):
        """
        Универсальное логирование действий (fallback, если Log/ActionType недоступны — молчим).
        """
        try:
            from .models import Log
            from django.contrib.auth import get_user_model

            User = get_user_model()
            staff = User.objects.filter(id=staff_id).first()

            if hasattr(Log, "ActionType"):
                # если не нашли точное значение в choices — пишем OTHER
                allowed = [c[0] for c in Log.ActionType.choices]
                action_value = action_type if action_type in allowed else Log.ActionType.OTHER
            else:
                action_value = action_type

            Log.objects.create(
                staff=staff,
                action_type=action_value,
                description_text=description,
                success_status=success,
            )
        except Exception:
            # Безопасно подавляем, чтобы не ронять основной поток (лог — вспомогательный)
            return

    # совместимость с вызовами _log_action
    _log_action = log_action
    
    @staticmethod
    def get_client_rental_history(client_id: int) -> List[Dict]:
        """Получить историю аренд клиента"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM get_client_rental_history(%s)", [client_id])
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
    
    @staticmethod
    def calculate_rental_cost(equipment_ids: List[int], start_date: date, end_date: date) -> Decimal:
        """Рассчитать стоимость аренды"""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT calculate_rental_cost(%s, %s, %s)",
                [equipment_ids, start_date, end_date]
            )
            return cursor.fetchone()[0]
    
    @staticmethod
    def calculate_late_fee(rent_id: int, penalty_rate: float = 0.1) -> Decimal:
        """Рассчитать пеню за просрочку"""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT calculate_late_fee(%s, %s)",
                [rent_id, penalty_rate]
            )
            return cursor.fetchone()[0]
    
    @staticmethod
    def generate_agreement_number() -> str:
        """Сгенерировать номер договора"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT generate_agreement_number()")
            return cursor.fetchone()[0]
        
    @staticmethod
    @transaction.atomic
    def create_rent_transaction(
        client_id: int,
        staff_id: int,
        equipment_ids: list,
        start_date: datetime,
        planned_end_date: datetime,
        total_amount: Decimal,
        rent_agreement_date: Optional[datetime] = None
    ):
        """
        Создание аренды в транзакции с использованием Django моделей
        """
        try:
            from django.contrib.auth import get_user_model
            from .models import Rent, RentItems, Equipment, Client

            User = get_user_model()

            client = Client.objects.get(id=client_id)
            staff = User.objects.get(id=staff_id)
            
            agreement_number = Rent.generate_agreement_number()
            
            if not rent_agreement_date:
                rent_agreement_date = timezone.now().date()
            
            unavailable_equipment = []
            for equipment_id in equipment_ids:
                try:
                    equipment = Equipment.objects.get(id=equipment_id)
                    if equipment.status != 'available':
                        unavailable_equipment.append(
                            f"{equipment.equipment_name} (ID: {equipment.id})"
                        )
                except Equipment.DoesNotExist:
                    unavailable_equipment.append(f"Оборудование ID: {equipment_id} не найдено")
            
            if unavailable_equipment:
                raise ValidationError(
                    f"Следующее оборудование недоступно или не найдено: {', '.join(unavailable_equipment)}"
                )
            
            rent = Rent.objects.create(
                client=client,
                staff=staff,
                rent_agreement_number=agreement_number,
                rent_agreement_date=rent_agreement_date,
                start_date=start_date,
                planned_end_date=planned_end_date,
                rent_status='active',
                total_amount=total_amount,
                is_paid=False
            )
            
            for equipment_id in equipment_ids:
                equipment = Equipment.objects.select_for_update().get(id=equipment_id)
                
                RentItems.objects.create(rent=rent, equipment=equipment)
                
                equipment.status = 'rented'
                equipment.save(update_fields=['status'])
            
            RentalService._log_action(
                staff_id, 
                'CREATE', 
                f'Создана аренда #{rent.id} ({agreement_number}). '
                f'Клиент: {client.email}. Оборудование: {len(equipment_ids)} ед.'
            )
            
            return rent
            
        except ValidationError:
            raise
        except Exception as e:
            RentalService._log_action(
                staff_id, 
                'CREATE', 
                f'Ошибка создания аренды: {str(e)}', 
                False
            )
            raise ValidationError(f"Ошибка создания аренды: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def complete_rent_with_transaction(rent_id, actual_end_date, staff_id):
        """
        Завершение аренды в транзакции
        """
        try:
            from .models import Rent, RentItems, Equipment
            
            rent = Rent.objects.select_for_update().get(id=rent_id)
            
            rent.actual_end_date = actual_end_date
            rent.rent_status = 'completed'
            rent.save()
            
            rent_items = RentItems.objects.filter(rent=rent).select_related('equipment')
            for item in rent_items:
                item.equipment.status = 'available'
                item.equipment.save()
            
            RentalService.log_action(staff_id, 'UPDATE', f'Завершена аренда #{rent.id}')
            
            return rent
            
        except Exception as e:
            RentalService.log_action(staff_id, 'UPDATE', f'Ошибка завершения аренды: {str(e)}', False)
            raise



def get_client_history(client_id: int) -> List[Dict]:
    return RentalService.get_client_rental_history(client_id)

def calculate_rent_cost(equipment_ids: List[int], start_date: date, end_date: date) -> Decimal:
    return RentalService.calculate_rental_cost(equipment_ids, start_date, end_date)

class BulkOperationsService:
    
    @staticmethod
    @transaction.atomic
    def bulk_update_equipment_status(equipment_ids, new_status, staff_id):
        """
        Массовое обновление статусов оборудования
        """
        try:
            from .models import Equipment
            
            equipment_list = Equipment.objects.filter(
                id__in=equipment_ids
            ).select_for_update()
            
            updated_count = equipment_list.update(status=new_status)
            
            RentalService.log_action(
                staff_id,
                'CHANGE_STATUS',
                f'Массовое обновление статусов: {updated_count} единиц оборудования на "{new_status}"',
                True
            )
            
            return updated_count
            
        except Exception as e:
            RentalService.log_action(
                staff_id,
                'CHANGE_STATUS',
                f'Ошибка массового обновления статусов: {str(e)}',
                False
            )
            raise

class PaymentService:
    
    @staticmethod
    @transaction.atomic
    def process_payment(rent_id, payment_data, staff_id):
        """
        Обработка платежа в транзакции
        """
        try:
            from .models import Rent
            
            rent = Rent.objects.select_for_update().get(id=rent_id)
            
            if rent.is_paid:
                raise ValidationError("Аренда уже оплачена")
            
            rent.is_paid = True
            rent.payment_method = payment_data.get('payment_method')
            rent.transaction_number = payment_data.get('transaction_number')
            rent.payment_date = payment_data.get('payment_date', timezone.now().date())
            rent.save()
            
            RentalService.log_action(
                staff_id, 
                'UPDATE', 
                f'Оплачена аренда #{rent_id}. Сумма: {rent.total_amount}',
                True
            )
            
            return rent
            
        except Exception as e:
            RentalService.log_action(
                staff_id, 
                'UPDATE', 
                f'Ошибка оплаты аренды #{rent_id}: {str(e)}',
                False
            )
            raise
