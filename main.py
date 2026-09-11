from django.template.defaultfilters import length

text = "jsvayv @hvewgjyqghbd evyjqgdb @cyuwcbnx wjevfygbxi uejygdb"
listt=text.split()
a=[]
for i in listt:
    if i.startswith('@'):
        a.append(i[1:])

print(a)