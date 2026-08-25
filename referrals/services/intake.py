from django.db import transaction

from ..models import ReferralRequest, ReferralSession
from ..serializers import ReferralRequestSerializer


def finalize_session(session: ReferralSession) -> ReferralRequest:
    """Create and link a ReferralRequest from a completed session draft.

    The operation is idempotent: calling it again for a completed session
    returns the existing referral instead of creating a duplicate.
    """
    with transaction.atomic():
        locked_session = (
            ReferralSession.objects
            .select_for_update()
            .get(pk=session.pk)
        )

        if locked_session.referral_request_id:
            return locked_session.referral_request

        if locked_session.status == ReferralSession.Status.ABANDONED:
            raise ValueError("Cannot finalize an abandoned referral session.")

        serializer = ReferralRequestSerializer(data=locked_session.draft)
        serializer.is_valid(raise_exception=True)
        referral = serializer.save()

        locked_session.referral_request = referral
        locked_session.status = ReferralSession.Status.COMPLETED
        locked_session.save(
            update_fields=["referral_request", "status", "updated_at"]
        )

        return referral
