# LogWatcher - An Enhanced Log Watch Tool with Custom Filtering

Event logs of multiple systems can be sent to a remote log server for central management. Usually logs are text files without structure. Most of the logs are about usual activities and irrelevant for a system administrator. Filtering the logs for relevant events based on the content is essential in a central log management software.

LogWatcher is a small prototype of this type of a customizable log management software. Logs coming from different hosts and facilities are filtered and watched by user. User is able to define custom rules for a log filter and incoming log source will be applied to these rules and matching log entries will be displayed in an online environment (immediately).

Each log filter object has its own set of rules to match a log entry based on:
* IP of the host generating the log
* Log severity (debug, info, notice, error, critical, etc)
* Log facility (mail, kernel, daemon, ...)
* Fields in log body (seperated by a predefine seperator)
* Parts in log body to be found with given regular expressions

A filter match can be defined on equality, inequality, substring or regular expression based. Filter rules can be combined with logic operators conjunction and disjunction. In other words a filtering object ruleset will be a tree with rules at the leaves and logical operators in the nodes. User should be able to define a log resource (a file or a socket) and a ruleset in a filtering object. Then, as a new log matches the filter, it can be observed (read) by the user.

## Internal Details

The filtering rules have a tree structure of user's choice since AND and OR operators can be used to combine match expressions. In order to edit this tree, user needs to address an arbitrary node or leaf. A path based addressing can be in form of list of binary branch choices as (0,1,1,0) denoting left, right, right, and left branch is traversed to get a subtree. The null tuple () denotes the root tree.

The match value is a n-tuple in the form (```matchfield```, ```operator```, ```value```, ```negated```, ```caseinsens```). 

```matchfield``` is one of ```WHOLE```, ```IP```, ```SEVERITY```, ```FACILITY```, ```FIELD:range:sep```, ```RE:regexp:field```. ```WHOLE``` matches the whole normalized syslog message. ```IP``` is ip number or hostname specified in the log. For ```SEVERITY``` and ```FACILITY``` comparison was made based on manual pages of syslog. The ```FIELD``` is followed by a range description, either a single number two numbers seperated by a dash. the last subfield is the separator symbol. For example ```FIELD:2-5:```, will seperate log line with ```,```, compose a substring from field 2 (starting from 0) to 5 inclusive and match that string. ```RE:regexp:field``` passes syslog message on a regular expression substitute and subtitutes it with the given field. This way message body extracts the regular expression based group. The value is simply: ```re.sub(regexp, '\g<' + field + '>',  message)```. 

```operator``` is one of EQ, LT, LE, GT, GE, or RE. RE is used for regular expression match assuming value is a regular expression. All the others are comparison operators. ```value``` is the other operand of the operator. First operand is the log component. If ```negated``` is True the calculated match value is reversed. If ```caseinsens``` is true all matches are case insensitive, values are converted to lowercase and than compared.

## How to run?

Start Django development server and start ```watcher/logwatch_manager.py```, after that you can login from browser and create LogWatch objects which will listen incoming logs from 5140 port. For a demo, one can use ```watcher/tests/demo.txt```.