import datetime
import re

from scsl.names import fix_name

class Section(object):
    def __init__(self, title):
        self.title = title

class Speech(object):
    # Some state variables
    current_time = None
    current_section = None
    witness = None

    def __init__(self, speaker, text):
        self.speaker = speaker
        self.text = [ [ text ] ]
        self.time = self.current_time
        self.section = self.current_section

    def add_para(self, text):
        self.text.append([ text ])

    def add_text(self, text):
        self.text[-1].append(text)

    @classmethod
    def reset(cls):
        cls.current_time = None
        cls.current_section = None

def parse_transcript(text, date):
    print "PARSING %s" % date

    page, num = 1, 1

    speech = None
    Speech.reset()

    interviewer = None
    state = 'text'
    for line in text:
        # Page break
        if '\014' in line:
            page += 1
            num = 1
            if date == datetime.date(2006, 9, 22) and page == 2:
                # No line 1 here
                num = 2
            continue

        # Empty line
        if re.match('\s*$', line):
            continue

        # Start of index, ignore from then on
        if re.search('I N D E X$', line) or state == 'index':
            state = 'index'
            continue

        if page == 1:
            # Title page
            line = line.strip()

            time_row = 7
            heading_row = 8
            location_row = 9
            if date.isoformat() == '2008-03-06':
                time_row = 8
                heading_row = 7
            if date.isoformat() in ('2007-07-03', '2007-06-25'):
                heading_row = None
                location_row = 8

            if num == 1:
                if line in ('Case No. SCSL-', 'SCSL-2003-', '2003-01-', '01-PT'):
                    # Special case for one day that prints the ID over four lines in bits
                    if line == '01-PT': num += 1
                    continue
                else:
                    assert re.match('Case No. SCSL-2003-01-([AT]|PT)', line), line
            elif num == 2:
                if line == 'THE PROSECUTOR OF SPECIAL COURT':
                    num += 1
                else:
                    assert line in ('THE PROSECUTOR OF', 'THE PROSECUTOR OF THE'), line
            elif num == 3:
                assert line in ('THE SPECIAL COURT', 'SPECIAL COURT'), line
            elif num == 4:
                assert 'V.' == line, line
            elif num == 5:
                assert line in ('CHARLES GHANKAY TAYLOR', 'CHARLES GHANKAY TAYLOR.'), line
            elif num == 6:
                def try_a_format(s, f):
                    try:
                        return datetime.datetime.strptime(s, f).date()
                    except ValueError:
                        return False
                for f in ('%A, %d %B %Y', '%A,%d %B %Y', '%d %B %Y'):
                    DATE = try_a_format(line, f)
                    if DATE: break
                if not DATE: raise Exception
                if date != DATE: raise Exception, '%s %s' % (date, DATE)
            elif num == time_row:
                line = re.sub('a\.m\.?(?i)', 'am', line)
                line = re.sub('p\.m\.?(?i)', 'pm', line)
                try:
                    datetime.datetime.strptime(line, '%I.%M %p')
                except:
                    datetime.datetime.strptime(line, '%I:%M %p')
            elif num == heading_row:
                assert line.upper() in ('ORAL HEARING', 'APPEALS JUDGEMENT',
                    'STATUS CONFERENCE', 'SENTENCING HEARING', 'JUDGEMENT',
                    'HEARING', 'DEFENCE FINAL SUBMISSIONS',
                    'PROSECUTION FINAL SUBMISSIONS', 'PROCEEDINGS',
                    'TRIAL', 'PROSECUTION OPENING STATEMENT',
                    'PRE-TRIAL CONFERENCE', 'INITIAL APPEARANCE'), line
            elif num == location_row:
                assert line in ('APPEALS CHAMBER', 'TRIAL CHAMBER II', 'TRIAL CHAMBER II.'), line
                LOCATION = line.replace('.', '')
            #else:
            #    print line

            num += 1
            continue

        # Ignore page headers/footers (except to get page number, check date, etc!)
        m1 = re.match('(?i)(CHARLES TAYLOR|CHARLES GHANKAY TAYLOR|TAYLOR|ACCUSED NAME) * (?:Page )?(\d+)(?: *PAG)?$', line.strip())
        m2 = re.match('2[23].01.2013 * (\d+)$', line.strip())
        m = m1 or m2
        if m:
            PAGE = m.group(1)
            continue
        date_fmt1 = date.strftime('%d %B %Y').lstrip('0')
        date_fmt2 = date.strftime('%B %d,%Y').lstrip('0')
        if re.match('(?i)(DATE|0?' + date_fmt1 + '|' + date_fmt2 + ') * (OPEN OR CLOSED|OPEN|CLOSED|PRIVATE) SESSION', line.strip()):
            continue
        if re.match('Special Court for Sierra Leone *\(Open Session\) *SCSL 2003-01-A$', line.strip()):
            continue
        # Special case bad headings on this date
        if date == datetime.date(2007, 7, 3):
            if re.sub(' +', ' ', line.strip()) in ('3', 'OPEN', '3 OPEN', 'SESSION', '2 JULY 2007', '2 JULY 2007 OPEN'):
                continue
        if re.match('(?i)SCSL - (APPEALS CHAMBER|TRIAL CHAMBER II|TRIAL CHAMBER)', line.strip()):
            continue

        m = re.match('(\d\d:\d\d:\d\d) (\d+)  ', line.strip())
        if m:
            TIME = m.group(1)
            line = line.replace(m.group(0), '           ' + m.group(2))
        m = re.match('(\d\d:\d\d:\d\d) ', line.strip())
        if m:
            TIME = m.group(1)
            line = line.replace(TIME, '        ')

        # Let's check we haven't lost a line anywhere...
        assert re.match(' *%d( |$)' % num, line), '%s != %s' % (num, line)
        line = re.sub('^ *%d( |$)' % (num,), '', line)

        # Okay, here we have a non-empty, non-page number, non-index line of just text
        num += 1

        m = re.match('The Prosecutor of the Special Court v. Charles Ghankay Taylor', line.strip())
        if m:
            continue

        # Empty line
        if re.match('\s*$', line):
            continue

        # Date at start
        m = re.match(' *((Mon|Tues|Wednes|Thurs|Fri)day,? ?)?\d+ (August|September|October|November|December|January|February|March|April|May|June|July) (200[6-9]|201[0123])$', line)
        if m:
            continue

        # Headings
        # TODO - Are there any?
        #m = re.match('', line.strip())
        #if m:
        #    Speech.current_section = Section( title=line.strip() )
        #    continue

        # Continuation of multiline message
        if state == 'adjournment':
            speech.add_text(line.strip())
            if re.match(' *(.*)\]$', line):
                state = 'text'
            continue

        # Messages about lunch/adjournments
        if date.isoformat() == '2008-05-19':
            if re.match(' *\[Lunch break taken at 1.30 p.m.\] *\[Upon', line):
                line = line.replace('[Upon', '')
            if re.match(' *resuming at 2.30 p.m.\]', line):
                line = line.replace('resuming', '[Upon resuming')

        m = re.match('(?:\^ )?[\([].*[]\)]\.?$', line.strip())
        if m:
            yield speech
            speech = Speech( speaker=None, text=line.strip() )
            continue

        # Multiline messages
        if re.match(' *Monday. *\[Whereupon the hearing adjourned at', line):
            speech.add_text('Monday.')
            line = line.replace('Monday. ', '')
        m1 = re.match(' *\[(Due to|Whereupon|At this point|Proceedings adjourned)(?i)', line)
        m2 = re.match(' *(Whereupon the hearing adjourned at |Whereupon commencing at )', line)
        m = m1 or m2
        if m:
            yield speech
            state = 'adjournment'
            speech = Speech( speaker=None, text=line.strip() )
            continue

        # Questions
        m = re.match('(?:FURTHER )?(?:EXAMINATION-IN-CHIEF|CROSS-EXAMINATION|CROSS-EXAMINED|RE-EXAMINATION) BY ([A-Z ]*):?(?: *\[Cont(?:(?:inue|\')d|\.)\])?:?$', line.strip())
        if m:
            interviewer = fix_name(m.group(1))
            continue

        # Witness arriving
        m = re.match("(DANKPANNAH DR CHARLES GHANKAY TAYLOR):(?: \[Affirmed\])?$", line.strip())
        if m:
            Speech.witness = fix_name(m.group(1))
            Speech.current_section = Section( title=line.strip() )
            continue
        # TODO Witness is an ID number, needs list finding/ matching to name
        m = re.match("WITNESS: *([A-Z0-9- ]+):? \[(.*)\]\.?$", line.strip())
        if m:
            Speech.witness = fix_name(m.group(1))
            Speech.current_section = Section( title=line.strip() )
            continue

        if len(line)-len(line.lstrip()) > 11:
            print (len(line)-len(line.lstrip())), '*', line, '*'

        # Question/answer (speaker from previous lines)
        m = re.match('([QA])\. (.*)', line.strip())
        # On these dates, they only quote Q/As - but they quote elsewhere, which means it's getting it wrong TODO
        if m and date.isoformat() not in ('2011-03-09', '2011-03-10', '2011-03-11'):
            yield speech
            if m.group(1) == 'A':
                assert Speech.witness, line
                speaker = Speech.witness
            else:
                assert interviewer, line
                speaker = interviewer
            speech = Speech( speaker=speaker, text=m.group(2) )
            continue

        # New speaker, just name on a line
        m = re.match('(M[RS] [A-Z]+):$', line.strip())
        if m:
            interviewer = fix_name(m.group(1))
            continue

        # TODO "Presiding Judge" matching

        m = re.match(' *((?:[A-Z -]|De|Mc)+): (.*)', line)
        if m:
            yield speech
            speaker = fix_name(m.group(1))
            #if not interviewer:
            #    interviewer = speaker
            speech = Speech( speaker=speaker, text=m.group(2) )
            continue

        # TODO Check/sort paragraph indenting
        # 2/3 normal, 7+ new paragraph? Have to spot/deal with quoted text...

        # New paragraph if indent at least 8 spaces
        m = re.match('        ', line)
        if m:
            speech.add_para(line.strip())
            continue

        # If we've got this far, hopefully just a normal line of speech
        speech.add_text(line.strip())

    yield speech
