from django.db import connection
from typing import List, Dict, Optional
from datetime import date, datetime
from decimal import Decimal
from django.forms import ValidationError
from django.db import transaction
from django.utils import timezone

class RentalService:
    
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

            # Проверяем существование клиента и пользователя
            client = Client.objects.get(id=client_id)
            staff = User.objects.get(id=staff_id)
            
            # Генерируем номер договора
            agreement_number = Rent.generate_agreement_number()
            
            # Устанавливаем дату договора (по умолчанию - сегодня)
            if not rent_agreement_date:
                rent_agreement_date = timezone.now().date()
            
            # Проверяем доступность всего оборудования перед созданием аренды
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
            
            # Создаем запись аренды
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
                # actual_end_date, payment_date, payment_method, transaction_number - остаются NULL
            )
            
            # Создаем записи об оборудовании в аренде и обновляем статусы
            for equipment_id in equipment_ids:
                equipment = Equipment.objects.select_for_update().get(id=equipment_id)
                
                # Создаем связь аренда-оборудование
                RentItems.objects.create(rent=rent, equipment=equipment)
                
                # Обновляем статус оборудования
                equipment.status = 'rented'
                equipment.save(update_fields=['status'])
            
            # Логируем успешное создание
            RentalService._log_action(
                staff_id, 
                'CREATE', 
                f'Создана аренда #{rent.id} ({agreement_number}). '
                f'Клиент: {client.email}. Оборудование: {len(equipment_ids)} ед.'
            )
            
            return rent
            
        except ValidationError:
            # Перебрасываем ValidationError как есть
            raise
        except Exception as e:
            # Логируем другие ошибки
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
            
            # Обновляем аренду
            rent.actual_end_date = actual_end_date
            rent.rent_status = 'completed'
            rent.save()
            
            # Возвращаем оборудование
            rent_items = RentItems.objects.filter(rent=rent).select_related('equipment')
            for item in rent_items:
                item.equipment.status = 'available'
                item.equipment.save()
            
            # Логируем действие
            RentalService.log_action(staff_id, 'UPDATE', f'Завершена аренда #{rent.id}')
            
            return rent
            
        except Exception as e:
            RentalService.log_action(staff_id, 'UPDATE', f'Ошибка завершения аренды: {str(e)}', False)
            raise



# Удобные shortcuts
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
            
            # Блокируем все записи для обновления
            equipment_list = Equipment.objects.filter(
                id__in=equipment_ids
            ).select_for_update()
            
            updated_count = equipment_list.update(status=new_status)
            
            # Логируем массовое действие
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
            
            # Обновляем информацию о платеже
            rent.is_paid = True
            rent.payment_method = payment_data.get('payment_method')
            rent.transaction_number = payment_data.get('transaction_number')
            rent.payment_date = payment_data.get('payment_date', timezone.now().date())
            rent.save()
            
            # Логируем платеж
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
