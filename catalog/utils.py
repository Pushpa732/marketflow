from django.utils.text import slugify


def unique_slug(model, value, instance_pk=None, fallback="item"):
    """Turn a name into a URL-friendly slug that is not used by another row."""
    base_slug = slugify(value) or fallback
    slug = base_slug
    counter = 2

    queryset = model.objects.all()
    if instance_pk:
        queryset = queryset.exclude(pk=instance_pk)

    while queryset.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug