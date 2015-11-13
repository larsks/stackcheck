
     ____   ___    _   _  ___ _____   _   _ ____  _____ 
    |  _ \ / _ \  | \ | |/ _ \_   _| | | | / ___|| ____|
    | | | | | | | |  \| | | | || |   | | | \___ \|  _|  
    | |_| | |_| | | |\  | |_| || |   | |_| |___) | |___ 
    |____/ \___/  |_| \_|\___/ |_|    \___/|____/|_____|
                                                        


This project is just me noodling around with some thoughts about
configuration validation.  What I want is a declarative way to
describe the proper configuration of a system, rather than a specific
configuration file.  That means the solution needs to be able to (a)
validate configuration options that depend on other configuration
options, possibly in other files, and (b) it needs to be able to
validate the configuration against facts about the system (like amount
of memory, or number of processors, etc).

What I've put together is some very simple (fragile, untested, and
bad) code that uses [Augeas][] to parse a variety of configuration
files, and reads rules described in a YAML input file.

[augeas]: http://augeas.net/

## Examples

The following examples demonstrate my current vision of the rule
syntax.  There is sample data in the `example/` directory that you can
use to try these out.

The file `example/controller.yml` contains the rules referenced in
these examples.  The script `example/run-example` as the necessary
command line invocation to make sure things work, provided that you
have the necessary prerequisites installed.

### Example 1

You can try this out by running:

    cd example; ./run-example 01-bad-maxconn

In [KB 1595673][], Red Hat recommends that when putting [HAProxy][] in
front of [MariaDB][] that the the `maxconn` setting for  the proxy
match the `max_connections` setting for the database server.

[KB 1595673]: https://access.redhat.com/solutions/1595673
[haproxy]: http://www.haproxy.org/
[mariadb]: https://mariadb.org/

The following rule encapsulates this fact:

      - name: check that haproxy maxconn matches haproxy maxconn
        url: https://access.redhat.com/solutions/1595673
        vars:
          value_from_haproxy: /etc/haproxy/haproxy.cfg/listen[name="galera" or name="mariadb"]/maxconn
          value_from_mariadb: /etc/my.cnf.d/*[target="mysqld"]/target[. = "mysqld"]/max_connections
        assert: value_from_haproxy == value_from_mariadb
        message: >
          The maxconn setting used in the haproxy stanza for mariadb
          should match the MySQL max_connections setting.  Otherwise, 
          haproxy will use a default value of 2000 for the proxy 
          maxconn settings.

          Value in mariadb: {{value_from_mariadb}}

          Value in haproxy: {{value_from_haproxy|default('(not set)')}}

The `vars` section of the rule maps variable names to augeas [path
expressions][].  These variables are made available for use in the
`assert` directive, which uses the [Jinja2][] expression engine for
evaluation (which means you have access to all the standard Jinja2
filters and tests).

The `url` directive provides a link to documentation further
describing the recommended configuration.  One imagines that an HTML
output formatter could use this to provide contextual links.

[jinja2]: http://jinja.pocoo.org/

The `message` and `url` directives are used to display information in
the event that a test fails.  For example, using a simple console
output formatter, running the above test might result in:

    * check that haproxy maxconn matches haproxy maxconn: FAILED

        The maxconn setting used in the haproxy stanza for mariadb should
        match the MySQL max_connections setting.  Otherwise,  haproxy will
        use a default value of 2000 for the proxy  maxconn settings.

        Value in mariadb: 4096

        Value in haproxy: (not set)

[path expressions]: https://github.com/hercules-team/augeas/wiki/Path-expressions

### Example 2

You can try this out by running:

    cd example; ./run-example 02-bad-num-workers

Some configuration options need to be tuned based on facts about the
operating system environment.  For example, according to [KB 1990433][], the
the [nova][] `osapi_compute_workers` option should set to (the number
of processors * 3).  The following rule would validate this
configuration:

[nova]: https://wiki.openstack.org/wiki/Nova

[KB 1990433]: https://access.redhat.com/solutions/1990433

      - name: check that number of nova api workers is appropriate
        kburl: https://access.redhat.com/solutions/1990433
        vars:
          value: /etc/nova/nova.conf/DEFAULT/osapi_compute_workers
        assert: >
          value|default(facts.processors.count)|int
          == (facts.processors.count*3)
        message: >
          A default deployment of RHEL-OSP Director configures the number of 
          nova-api workers to three times the number of processors.  Your
          system has {{facts.processors.count}} processors, so this value
          should be set to {{facts.processors.count * 3 }}.

The facts available in the `facts` dictionary are provided by
[facter][], and are obtained either by running facter and parsing the
output or by using a cached copy of that output (which allows this
tool to be run somewhere other than on the live system).

[facter]: https://puppetlabs.com/facter

Running the above rule might result in output like:

    * check that number of nova api workers is appropriate: FAILED

        A default deployment of RHEL-OSP Director configures the number of
        nova-api workers to three times the number of processors.  Your
        system has 8 processors, so this value should be set to 24.

