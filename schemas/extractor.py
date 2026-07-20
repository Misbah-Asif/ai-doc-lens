from pydantic import BaseModel


class SalarySlipFields(BaseModel):
    document_name: str
    employee_name: str | None = None
    employer_name: str | None = None
    salary_month: int | None = None
    salary_year: int | None = None
    gross_salary: float | None = None
    net_salary: float | None = None
    currency: str | None = None
