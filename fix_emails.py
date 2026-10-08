import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_project.settings')
django.setup()

from news.models import CustomUser

print("Scanning for duplicate or empty emails...")

# Get ALL users
all_users = CustomUser.objects.all()
seen_emails = {}
updated_count = 0

for user in all_users:
    # Check if email is empty OR if we've seen this email before
    if not user.email or user.email in seen_emails:
        new_email = f"{user.username}_{user.id}@example.com"
        user.email = new_email
        user.save()
        print(f" -> Fixed {user.username}: {new_email}")
        updated_count += 1
    else:
        seen_emails[user.email] = True

if updated_count == 0:
    print("✅ All emails are already unique! You are good to go.")
else:
    print(f"\n🎉 Done! Fixed {updated_count} users. All emails are now unique.")