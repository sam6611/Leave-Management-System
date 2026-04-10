from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.leave_service import LeaveService
from app.services.rule_engine import RuleEngine
from app.services.cache_service import CacheService
from app.services.queue_service import QueueService
from app.services.notification_service import NotificationService

rule_engine = RuleEngine()
audit_service = AuditService()
cache_service = CacheService()
queue_service = QueueService()
notification_service = NotificationService()

leave_service = LeaveService(
    rule_engine=rule_engine,
    audit_service=audit_service,
    cache_service=cache_service,
    queue_service=queue_service,
    notification_service=notification_service,
)

auth_service = AuthService()