import re


re_year = re.compile(r' \d{4} ')
re_number = re.compile(r'\d')
re_pattern = re.compile(r'(.+?/|.+?[A-Za-z]{2,}[/\-\.~_]|.+?[A-Za-z\()][/\-\.~_]).*')


def extract(journal_text):
    jour = journal_text.partition(';')[0]
    if re_year.search(jour):
        jour = re_year.split(jour)[0].rstrip(' .(')
    jour = jour.replace('.','').lower()
    doi_pattern = re_number.sub('~', journal_text.partition('doi:')[2].partition('/')[2].partition(' ')[0])
    doi_small_pattern = re_pattern.sub(r'\1', doi_pattern)
    return jour, doi_small_pattern


# s = 'd~an~~~~-a.b.c-~'
# s = 's~~~~-~~~~(~~)~~~~~-x'
# s = '~~~~-~~~~.~~~~~~n~~~'
# s = '~~~~-~~~~/abaac~'
# s = '~~~~-~~~X/aba~~b'
# s = '~~~~-~~~X.~~~B~~.BJJ-~~~~-~~~~.R~'
# print(s)
# print(re_pattern.sub(r'\1', s))
# assert False
