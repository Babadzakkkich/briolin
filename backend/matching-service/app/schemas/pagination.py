from pydantic import BaseModel, Field


class PaginationInfo(BaseModel):
    """Информация о пагинации"""
    current_page: int = Field(1, description="Текущая страница")
    total_pages: int = Field(1, description="Всего страниц")
    total_results: int = Field(0, description="Всего результатов")
    page_size: int = Field(10, description="Размер страницы")

    @property
    def has_next(self) -> bool:
        return self.current_page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.current_page > 1