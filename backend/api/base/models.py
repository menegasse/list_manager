from django.db import models


class BaseModel(models.Model):
    """Base model."""

    class Meta:
        abstract = True

    id = models.BigAutoField(primary_key=True)  # noqa: A003

    def save(self, *, full_clean: bool = True, update_fields: list[str] | None = None, **kwargs):
        """Save the model in the database."""
        if full_clean:
            self.full_clean()
        return super().save(**kwargs)


class TimestampedMixin(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(
        verbose_name="Created at",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name="Updated at",
        auto_now_add=True,
    )
