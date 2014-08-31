from gringotts.checker import notifier
from gringotts.openstack.common import log


LOG = log.getLogger(__name__)


class LogNotifier(notifier.Notifier):

    @staticmethod
    def notify_has_owed(context, account, contact, projects):
        LOG.warn('account %s has owed, and the owed orders are: %s, account contact: %s'
                 % (account, projects, contact))

    @staticmethod
    def notify_before_owed(context, account, contact, projects, price_per_day, days_to_owe):
        LOG.warn('account %s will owe in %s days, daily consumption: %s, account contact: %s' %
                 (account, days_to_owe, price_per_day, contact))

    @staticmethod
    def notify_account_charged(context, account, contact, type, value, bonus=None):
        LOG.warn('account %s charged %s, system bonus: %s, contact: %s' %
                 (account, value, bonus, contact))
