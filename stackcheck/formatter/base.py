import abc


class Formatter (object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, verbose=None):
        self.verbose = verbose

    @abc.abstractmethod
    def start_run(self):
        '''This is called at the beginning of a
        validation run, before stackcheck has processed
        any rulesets.'''
        pass

    @abc.abstractmethod
    def stop_run(self):
        '''This is called at the conclusion of a 
        validation run, after stackcheck has processed
        all available rulesets.'''
        pass

    @abc.abstractmethod
    def start_ruleset(self, ruleset):
        '''This is called when stackcheck starts processing a 
        ruleset, before any rules have been evaluated.'''
        pass

    @abc.abstractmethod
    def stop_ruleset(self, ruleset):
        '''This is called after stackcheck has evaluated all
        the rules in a ruleset.'''
        pass

    @abc.abstractmethod
    def start_rule(self, rule):
        '''This is called when stackcheck encounters a new rule,
        before the rule has been evaluated.'''
        pass

    @abc.abstractmethod
    def stop_rule(self, rule, status, message=None):
        '''This is called after stackcheck has evaluated
        a rule.  `status` may be one of FAILED, OKAY,
        or SKIPPED.'''
        pass
