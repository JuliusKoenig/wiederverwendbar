import starlette_admin as sa


class CollectionField(sa.CollectionField):
    def _propagate_id(self) -> None:
        """Will update fields id by adding his id as prefix (ex: category.name)"""
        for field in self.fields:
            field.id = self.id + ("_" if self.id else "") + field.name
            if isinstance(field, type(self)):
                field._propagate_id()
