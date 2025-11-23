from rest_framework.schemas.openapi import AutoSchema


class TaggedAutoSchema(AutoSchema):
    """
    AutoSchema с поддержкой тегов/описаний/резюме на уровне ViewSet.
    Использует атрибуты:
      - schema_tags: список тегов OpenAPI
      - schema_description: описание ресурса
      - schema_component_name: базовое имя для operationId
      - schema_summaries: dict по actions ("list", "retrieve", "create", "update", "partial_update", "destroy")
    """

    def get_tags(self, path, method):
        view = self.view
        if getattr(view, "schema_tags", None):
            return view.schema_tags
        return super().get_tags(path, method)

    def get_description(self, path, method):
        view = self.view
        if getattr(view, "schema_description", None):
            return view.schema_description
        return super().get_description(path, method)

    def get_summary(self, path, method):
        view = self.view
        action = getattr(view, "action", "").lower()
        summaries = getattr(view, "schema_summaries", None)
        if summaries and action in summaries:
            return summaries[action]

        # fallback по типу метода
        default_summaries = {
            "get": "Получить ресурс",
            "post": "Создать ресурс",
            "put": "Полное обновление ресурса",
            "patch": "Частичное обновление ресурса",
            "delete": "Удалить ресурс",
        }
        return default_summaries.get(method.lower())

    def get_operation_id(self, path, method):
        view = self.view
        base_name = getattr(view, "schema_component_name", view.__class__.__name__)
        action = getattr(view, "action", method.lower())
        return f"{base_name}_{action}"
