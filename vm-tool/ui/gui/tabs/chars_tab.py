from .general_table_tab import GeneralTableTab


class CharsTab(GeneralTableTab):
    table_type = "chars"
    item_type_name = "字"

    def set_column_widths(self):
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)

    @property
    def search_method(self):
        return self.dict_service.search_characters

    @property
    def add_method(self):
        return self.dict_service.add_character

    @property
    def delete_method(self):
        return self.dict_service.delete_character

    @property
    def update_method(self):
        return self.dict_service.update_character

    @property
    def batch_add_params(self):
        return {"is_character": True}