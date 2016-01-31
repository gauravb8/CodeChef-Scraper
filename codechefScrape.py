import requests,shelve
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime
from notf import balloon_tip

                 
def scrapeSave(contests,shelfFile):
    """Accepts: contests, the html table tag for the table containing the contests on codechef page
                shelfFile, pointer to open shelve file containing contests list
       Navigates through the table to collect contest data and save it to the shelve file in list format
       Time Complexity : O(len(newEntries) + len(savedEntries))"""
    try:
        savedEntries=shelfFile['future']
    except:
        savedEntries=[]
    newEntries=[]                       ##This list will hold new contests that are to be shelved
    for tr in contests.children:
        if tr=='\n':        ##Omit blank elements(Found some of these while scraping from codechef!!)
            continue
        temp=[]
        ##Check if contest exists in stored database, if not add it to newEntries..
        if tr.td!=None and savedEntries !=[] and shelfFile.get(str(tr.td.getText().strip()),0)!=0 and shelfFile[str(tr.td.getText().strip())][0]==1:   
            continue

        i=1
        ##if code doesn't match,it means it is a new contest and we have to save it to our shelve file..
        for td in tr.children:                  ##Navigates to the children of 'table' element, ie. the 'tr' element and further navigates to the 'td' elements that contain actual data including code, name, start and end date. 
            if td!='\n' and td.name=='td':
                if i==1:
                    shelfFile[str(td.getText().strip())]=[1,0]          ##In [1,0], the first index denotes that the contest has been added, while the second index denotes whether it has been notified
                if i<=2:
                    temp.append(str(td.getText().strip()))
                else:
                    temp.append(datetime.strptime(td.getText().strip(),"%Y-%m-%d %H:%M:%S"))    ##parses string into datetime object.
                i+=1
        if temp!=[]:
            newEntries.append(temp)             ##Contest added to the list of new contests

    shelfFile['future']=newEntries+savedEntries  ##This writes the new contests to the beggining of the shelf file so as to retain the order
    return newEntries
    
def onGoing(shelfFile):
    """Accepts: The pointer to open File containing list of contests
       Returns: A list of contests currently in progress
       Works offline!"""
    contests=shelfFile['future']
    now=datetime.now()
    ongoing_contests=[]
    for contest in contests:
##        print contest[0]
        if shelfFile[contest[0]][1]==1:                 ##Checks if contest has been notified already.
            continue
        start=contest[2]
        end=contest[3]
        if now>=start and now<=end:
            ongoing_contests.append(contest)
    return ongoing_contests


def notify(present,callType,shelfFile):
    """Accepts : present, a list of currently ongoing contestss on codechef
                  callType, describes whether notification is for new added contest or ongoing contest
                  shelfFile, pointer to shelf file
        Notifies the user of the contests currently in progress"""
    if present!=[]:
        if callType=='ongoing':
            title="Ongoing contest on CodeChef"
        else:
            title="New contest added on CodeChef"
        
        for contest in present:
            msg=""
            print contest
            if callType=='ongoing':
                shelfFile[contest[0]]=[1,1]                 ##Sets contest as notified. This contest won't be notified again.
            msg+="Code : "+str(contest[0])
            msg+="\nName : "+str(contest[1])
            msg+="\nStarts on : "+contest[2].strftime("%dth %B, %Y")
            msg+="\nEnds on : "+contest[3].strftime("%dth %B, %Y")
            msg+='\n\n'
            balloon_tip(title,msg)

       
def delOldContests(shelfFile):
    """Deletes contests whose end date has passed"""
    try:
        contests=shelfFile['future']
    except:
        return
    relevantContests=[]
    now=datetime.now()
    for contest in contests:
        if contest[3]<now:
            del shelfFile[contest[0]]
        else:
            relevantContests.append(contest)
    shelfFile['future']=relevantContests

    
####Offline testing code..
##soup=BeautifulSoup(open('contestPage.html','r'), "html.parser")
##contests=soup.select('.table-questions')[0].table                    ##Selects the table containing rows of Future Contests...
##shelfFile=shelve.open('contests')            ##shelve file to store the info about contests
##delOldContests(shelfFile)
##scrapeSave(contests,shelfFile)
##present=onGoing(shelfFile)
##notify(present,'ongoing',shelfFile)
##shelfFile.close()

##Actual scraping code..
f=shelve.open('contests')
delOldContests(f)
f.close()
while True:
    shelfFile=shelve.open('contests')            ##shelve file to store the info about contests
    try:
        page=requests.get("https://www.codechef.com/contests")
        soup=BeautifulSoup(page.text, "html.parser")
        contests=soup.select('.table-questions')[0].table
        new=scrapeSave(contests,shelfFile)
        notify(new,'new',shelfFile)
    except Exception as e:
        print "Connection couldn't be established. ",e
    if shelfFile!={}:
        present=onGoing(shelfFile)
        notify(present,'ongoing',shelfFile)
    shelfFile.close()
    sleep(5)

