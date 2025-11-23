from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rental_system', '0004_equipment_image'),
    ]

    operations = [
        # Временный дроп зависящих вью, чтобы не блокировали изменение столбцов
        migrations.RunSQL(
            "DROP VIEW IF EXISTS staff_logs_view CASCADE; "
            "DROP VIEW IF EXISTS maintenance_schedule_view CASCADE;",
            reverse_sql="""
                -- staff_logs_view
                CREATE OR REPLACE VIEW staff_logs_view AS
                SELECT
                    u.id AS staff_id,
                    u.first_name,
                    u.last_name,
                    u.username,
                    l.log_date,
                    l.action_type,
                    l.success_status,
                    l.description_text
                FROM auth_user u
                LEFT JOIN rental_system_log l ON l.staff_id = u.id;

                -- maintenance_schedule_view
                CREATE OR REPLACE VIEW maintenance_schedule_view AS
                SELECT
                    m.id AS maintenance_id,
                    m.maintenance_date,
                    e.id AS equipment_id,
                    e.equipment_name,
                    u.id AS staff_id,
                    u.first_name,
                    u.last_name,
                    m.description,
                    m.status
                FROM rental_system_maintenance m
                JOIN rental_system_equipment e ON m.equipment_id = e.id
                LEFT JOIN auth_user u ON m.staff_id = u.id
                ORDER BY m.maintenance_date;
            """,
        ),
        migrations.AlterField(
            model_name='log',
            name='staff',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='maintenance',
            name='staff',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='rent',
            name='staff',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='Staff',
        ),
        # Восстанавливаем вьюхи с новой схемой
        migrations.RunSQL(
            """
            CREATE OR REPLACE VIEW staff_logs_view AS
            SELECT
                u.id AS staff_id,
                u.first_name,
                u.last_name,
                u.username,
                l.log_date,
                l.action_type,
                l.success_status,
                l.description_text
            FROM auth_user u
            LEFT JOIN rental_system_log l ON l.staff_id = u.id;

            CREATE OR REPLACE VIEW maintenance_schedule_view AS
            SELECT
                m.id AS maintenance_id,
                m.maintenance_date,
                e.id AS equipment_id,
                e.equipment_name,
                u.id AS staff_id,
                u.first_name,
                u.last_name,
                m.description,
                m.status
            FROM rental_system_maintenance m
            JOIN rental_system_equipment e ON m.equipment_id = e.id
            LEFT JOIN auth_user u ON m.staff_id = u.id
            ORDER BY m.maintenance_date;
            """,
            reverse_sql="""
            DROP VIEW IF EXISTS staff_logs_view;
            DROP VIEW IF EXISTS maintenance_schedule_view;
            """,
        ),
    ]
