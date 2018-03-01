import re


# <start id="tokenize-and-index"/>
STOP_WORDS = set('''able about across after all almost also am among
an and any are as at be because been but by can cannot could dear did
do does either else ever every for from get got had has have he her
hers him his how however if in into is it its just least let like
likely may me might most must my neither no nor not of off often on
only or other our own rather said say says she should since so some
than that the their them then there these they this tis to too twas us
wants was we were what when where which while who whom why will with
would yet you your'''.split())                                          #A

WORDS_RE = re.compile("[a-z']{2,}")                                     #B

def tokenize(content):
    words = set()                                                       #C
    for match in WORDS_RE.finditer(content.lower()):                    #D
        word = match.group().strip("'")                                 #E
        if len(word) >= 2:                                              #F
            words.add(word)                                             #F
    return words - STOP_WORDS                                           #G 这个减法操作看起来很上流。

def index_document(conn, docid, content):
    words = tokenize(content)                                           #H

    pipeline = conn.pipeline(True)
    for word in words:                                                  #I
        pipeline.sadd('idx:' + word, docid)                             #I
    return len(pipeline.execute())                                      #J