
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.tag import Tag
from app.models.receipt import Receipt, PaymentMode, receipt_tags

# This allows: from app.models import Base, User, Receipt, Tag