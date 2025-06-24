from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

GENERIC_CHOICES = [
    (0, "Disabled"),
    (1, "Enabled")
]

SPAM_FILTER_CHOICES = [
    (0, "Disabled"),
    (1, "Delete"),
    (2, "Warn")
]

WARN_LIMIT_CHOICES = [
    (0, "Disabled"),
    (1, "Notify"),
    (2, "Kick"),
    (3, "Ban")
]

SHOW_PFP_CHOICES = [
    (0, "No Picture"),
    (1, "Small Picture"),
    (2, "Large Picture")
]


class Owners(models.Model):
    user_id = models.BigIntegerField(primary_key=True, db_index=True)
    user_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Owner"
        verbose_name_plural = "Owners"


class UserConfig(models.Model):
    translate_private = models.BooleanField(default=False)  # type: ignore
    fact_check_private = models.BooleanField(default=False)  # type: ignore
    
    class Meta:
        verbose_name = "User configuration"
        verbose_name_plural = "User configurations"


class FavouriteTracks(models.Model):
    title = models.CharField(max_length=200, null=True, blank=True)
    url = models.URLField(db_index=True)
    duration = models.CharField(max_length=20, null=True, blank=True)
    uploader = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Favourite Track"
        verbose_name_plural = "Favourite Tracks"


class FavouritePlaylists(models.Model):
    title = models.CharField(max_length=200, null=True, blank=True)
    url = models.URLField(db_index=True)
    count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    uploader = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Favourite Playlist"
        verbose_name_plural = "Favourite Playlists"


class Users(models.Model):
    user_id = models.BigIntegerField(primary_key=True, db_index=True)
    user_name = models.CharField(max_length=255, db_index=True)
    global_name = models.CharField(max_length=255, null=True, blank=True)
    avatar_url = models.URLField(null=True, blank=True)
    
    config = models.OneToOneField(UserConfig, on_delete=models.CASCADE, related_name="user")
    
    favourite_tracks = models.ManyToManyField(FavouriteTracks, blank=True, related_name="users")
    favourite_playlists = models.ManyToManyField(FavouritePlaylists, blank=True, related_name="users")

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class GuildConfig(models.Model):
    # Auto role
    auto_role_active = models.IntegerField(
        choices=GENERIC_CHOICES,
        default=0,  # type: ignore
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    auto_role_id = models.BigIntegerField(null=True, blank=True)
    auto_role_name = models.CharField(max_length=255, null=True, blank=True)
    
    # Spam filter
    spam_filter_action = models.IntegerField(
        choices=SPAM_FILTER_CHOICES,
        default=0,  # type: ignore
        validators=[MinValueValidator(0), MaxValueValidator(2)]
    )
    spam_filter_message = models.TextField(null=True, blank=True)
    spam_filter_original_state = models.IntegerField(
        default=0,  # type: ignore
        choices=SPAM_FILTER_CHOICES,
        validators=[MinValueValidator(0), MaxValueValidator(2)]
    )
    
    # Warn limit
    warn_limit = models.IntegerField(
        default=6,  # type: ignore
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    warn_action = models.IntegerField(
        choices=WARN_LIMIT_CHOICES,
        default=0,  # type: ignore
        validators=[MinValueValidator(0), MaxValueValidator(3)]
    )
    warn_action_original_state = models.IntegerField(
        default=0,  # type: ignore
        choices=WARN_LIMIT_CHOICES,
        validators=[MinValueValidator(0), MaxValueValidator(3)]
    )
    
    # Translate
    translate = models.IntegerField(
        choices=GENERIC_CHOICES,
        default=0,  # type: ignore
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    translate_lang = models.CharField(default="en")
    
    # Welcome channel
    welcome_active = models.IntegerField(
        choices=GENERIC_CHOICES,
        default=0,  # type: ignore
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    welcome_channel_id = models.BigIntegerField(null=True, blank=True)
    welcome_channel_name = models.CharField(max_length=100, null=True, blank=True)
    welcome_title = models.CharField(max_length=200, null=True, blank=True)
    welcome_description = models.TextField(null=True, blank=True)
    welcome_colour = models.CharField(max_length=7, default="#FFFFFF")
    welcome_show_pfp = models.IntegerField(
        choices=SHOW_PFP_CHOICES,
        default=0,  # type: ignore
        validators=[MinValueValidator(0), MaxValueValidator(2)]
    )
    
    class Meta:
        verbose_name = "Guild configuration"
        verbose_name_plural = "Guild configurations"


class Warns(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="warns")
    moderator = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True, related_name="warns_issued")
    reason = models.TextField()
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    is_active = models.BooleanField(default=True)  # type: ignore
    
    class Meta:
        verbose_name = "Warn"
        verbose_name_plural = "Warns"
        indexes = [
            models.Index(fields=["user", "date"]),
        ]


class Guilds(models.Model):
    guild_id = models.BigIntegerField(primary_key=True, db_index=True)
    guild_name = models.CharField(max_length=255, db_index=True)
    guild_icon_url = models.URLField(null=True, blank=True)
    
    config = models.OneToOneField(GuildConfig, on_delete=models.CASCADE, related_name="guild")
    
    users = models.ManyToManyField(Users, blank=True, related_name="guilds")
    admins = models.ManyToManyField(Users, blank=True, related_name="guilds_admins")
    blacklist = models.ManyToManyField(Users, blank=True, related_name="guilds_blacklist")
    warns = models.ManyToManyField(Warns, blank=True, related_name="guilds")

    class Meta:
        verbose_name = "Guild"
        verbose_name_plural = "Guilds"