#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 28 16:15:25 2019

@author: erkamozturk
"""

from Tkinter import *
from bs4 import BeautifulSoup
import urllib2
from django.utils.encoding import smart_str
import tkMessageBox
import shelve
import time
ignorewords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])


class ProjectAnalyzer(Frame):

    def __init__(self, root):
        Frame.__init__(self, root)
        self.root = root
        self.widgets()
        self.geometricDesign()

    def widgets(self):
        self.frame1 = Frame(self.root)
        self.frame2 = Frame(self.root)
        self.frame3 = Frame(self.root)
        self.title = Label(self.frame1, text="SEHIR Scholar", font="times 11 bold ",
                           bg="darkblue", fg="white", width=70,height=2)
        self.url=Label(self.frame1,text="Url for faculty list:",pady=20)
        self.entry=Entry(self.frame1, bg="white", width=30)
        self.entry.insert(0, 'http://cs.sehir.edu.tr/en/people/')
        self.build=Button(self.frame1,text="Build Index", command=self.fetch)
        self.keyword=Entry(self.frame1,bg="white",width=50)
        self.search = Button(self.frame1, bg='white', text='Search', command=self.search)
        self.ranking=Label(self.frame1,text="Ranking Criteria")
        self.weight=Label(self.frame1,text="Weight")
        self.filter=Label(self.frame1,text="Filter Papers")
        self.WordFreq=IntVar()
        self.word=Checkbutton(self.frame1, text="Word Frequency", variable=self.WordFreq)
        self.CitCount = IntVar()
        self.citation1=Checkbutton(self.frame1, text="Citation Count", variable=self.CitCount)
        self.wordweight=Entry(self.frame1,width=2)
        self.wordweight.insert(0,'1')
        self.citationweight=Entry(self.frame1,width=2)
        self.citationweight.insert(0, '1')
        self.papers=Listbox(self.frame1,height=5, selectmode ='multiple', font='Tahoma')
        self.scrollbar = Scrollbar(self.frame2)
        self.text = Text(self.frame2, bg="white", height=16, width=100, yscrollcommand=self.scrollbar.set)
        self.previous = Button(self.frame3, text="Previous")
        self.pagenumber = Label(self.frame3, text=" 1 ")
        self.pagenumber.config(background="blue", foreground="white", bd=3, relief=SUNKEN)
        self.next_ = Button(self.frame3, text="Next")
        self.page = Label(self.frame3, text="Page:")

    def fetch(self):

        url = self.entry.get()  # get the url
        response = urllib2.urlopen(
            url)  # type instance; when we print, <addinfourl at 50382568 whose fp = <socket._fileobject object at 0x0300ACB0>>
        html = response.read()  # type str, all page in str
        soup = BeautifulSoup(html, 'html.parser')  # parse it
        all_Data = soup.findAll('div', {'class': 'member'})  # we need just div lass id member

        members_links=[]
        for prj in all_Data:
            a = 'http://cs.sehir.edu.tr/'+prj.find('a').get('href')  # we got the full links for go to specofoc page
            members_links.append(a)

        datas = {}
        for link in members_links:

            response = urllib2.urlopen(link)
            html = response.read()  # type str, all page in str
            soup = BeautifulSoup(html, 'html.parser')
            all_Data = soup.find('div', {'id': 'publication'})  # we need to go in p's
            ps_list=[]
            ps=all_Data.find_all('p')  # and get the citation types
            for p in ps:
                # we got the types like book chapters, journal papers
                ps_list.append(p.text.strip())

            all_ul=all_Data.find_all('ul')
            for index,ul in enumerate(all_ul):  # for getting both index
                all_li=ul.find_all('li')
                for li in all_li:
                    paper = li.text.split('\n')[2]  # Mehmet Serkan Apaydn, Douglas L Brutlag, Carlos Guestrin, David Hsu, Jean-Claude Latombe:

                    try:
                        citetion = li.find('a').text.split('\n')[1].strip().strip('[')  # strip for clening the speces split for for separate

                    except AttributeError: citetion=0

                    datas[paper]=(citetion,ps_list[index])  # we got in one dict what we need

                    self.datas = datas
                    self.paper = paper

        self.wordlocation = shelve.open('ayse.db', writeback=True, flag='c')  # and create the dbs
        self.citation  = shelve.open('erkam.db', writeback=True, flag='c')  # and create the dbs
        self.citation_number = shelve.open('yesim.db', writeback=True, flag='c')  # and create the dbs

        for key in datas:

            words = self.separatewords(key)

            self.citation[smart_str(key)] = datas[key][1]   # we create for citation number
            self.citation_number[smart_str(key)] = float(datas[key][0])  # and citation type


            for index,word in enumerate(words):

                word = smart_str(word)
                if word in ignorewords:
                    continue

                self.wordlocation.setdefault(word, {})
                self.wordlocation[word].setdefault(smart_str(key), [])
                self.wordlocation[word][smart_str(key)].append(index)  # we keep the index = where are words

        direct_list = []
        for i in self.citation.values():
            if i not in direct_list:
                direct_list.append(i)
        for i in direct_list:  # for fulling listbox
            self.papers.insert(END, str(i))

    def search(self):  # this is our search engine
        start_time = time.time()  # for getting time
        which_words = self.keyword.get()

        if which_words != '':

            self.active_row = self.papers.curselection()  # get which one is active it will give tuples

            self.values = [self.papers.get(idx) for idx in self.active_row]

            self.query(which_words)  # go to find the input
        else:

            tkMessageBox.showerror("Error",
                                   "Please provide at least one keyword.")

        end_time = time.time()
        self.elapsedTime = end_time - start_time
        self.time_table = Label(self.frame2, bg="white", text=str(end_time) + ' seconds', fg='red').grid(row=0,
                                                                                                         column=0,
                                                                                                         pady=10)

    def query(self, q):  # from lecturer codes we will play litte for getting the current format

        self.text.delete('1.0', END)
        self.results, self.words = self.getmatchingpages(q)
        # print self.results
        if len(self.results) == 0:
            print 'No matching pages found!'
            return

        try:  # try excepts for getting tk messages boxs

            try:
                scores = self.getscoredlist(self.results, self.words)
                rankedscores = sorted([(score, url) for (url, score) in scores.items()], reverse=1)

                i = 0
                for (score, url) in rankedscores[0:10]:

                    if self.citation[url] in self.values:

                        key = str(i + 1) + '.     %s\t%f' % (url, score)

                        self.text.insert(END, key)
                        self.text.insert(END, '\n')
                        self.text.insert(END, '\n')
                        i = i + 1

                    elif len(self.values) == 0:

                        tkMessageBox.showerror("Error",
                                               "Please  choose at least one paper category.")
                        break

            except ValueError:
                tkMessageBox.showerror("Error",
                                       "Please provide the weights if multiple ranking measure is selected.")
        except AttributeError:

            tkMessageBox.showerror("Error",
                                   "Please choose at least one ranking measure")

    def getmatchingpages(self, q):   # for lecturer codes

        results = {}
        # Split the words by spaces
        words = [smart_str(word) for word in q.split()]
        if words[0] not in self.wordlocation:
            return results, words

        url_set = set(self.wordlocation[words[0]].keys())

        for word in words[1:]:
            if word not in self.wordlocation:
                return results, words
            url_set = url_set.intersection(self.wordlocation[word].keys())

        for url in url_set:
            results[url] = []
            for word in words:
                results[url].append(self.wordlocation[word][url])

        return results, words

    def getscoredlist(self, results, words):  # it calculates the both freqency and citation scores and if loops okay, it will plus both of them
        totalscores = dict([(url, 0) for url in results])

        # This is where you'll later put the scoring functions
        weights = []

        # word frequency scoring

        if self.WordFreq.get() == 1 and self.CitCount.get() == 1:

            weights = [(float(self.wordweight.get()), self.frequencyscore(results)),
                       (float(self.citationweight.get()), self.citentionscore(results))]
            #            (1.0, self.inboundlinkscore(results))]

            for (weight, scores) in weights:
                for url in totalscores:
                    totalscores[url] += weight * scores.get(url, 0)

            return totalscores

        elif self.WordFreq.get() == 1:

            weights = [(float(self.wordweight.get()), self.frequencyscore(results)),
                       (float('0'), self.citentionscore(results))]
            #            (1.0, self.inboundlinkscore(results))]

            for (weight, scores) in weights:
                for url in totalscores:
                    totalscores[url] += weight * scores.get(url, 0)

            return totalscores

        elif self.CitCount.get() == 1:

            weights = [(float('0'), self.frequencyscore(results)),
                       (float(self.citationweight.get()), self.citentionscore(results))]
            #            (1.0, self.inboundlinkscore(results))]

            for (weight, scores) in weights:
                for url in totalscores:
                    totalscores[url] += weight * scores.get(url, 0)

            return totalscores

    def citentionscore(self, results):   # it calculates the citation score
        counts = {}
        for paper in results:
            score = self.citation_number[paper]
            counts[paper] = score

        return self.normalizescores(counts, smallIsBetter=False)

    def frequencyscore(self, results):  # for calculating frequency score
        counts = {}
        for url in results:
            score = 1
            for wordlocations in results[url]:
                score *= len(wordlocations)
            counts[url] = score
        return self.normalizescores(counts, smallIsBetter=False)

    def normalizescores(self, scores, smallIsBetter=0):  # from lecturer codes it will nirmalzie our score o to 1
        vsmall = 0.00001  # Avoid division by zero errors
        if smallIsBetter:
            minscore = min(scores.values())
            minscore = max(minscore, vsmall)
            return dict([(u, float(minscore) / max(vsmall, l)) for (u, l) \
                         in scores.items()])
        else:
            maxscore = max(scores.values())
            if maxscore == 0:
                maxscore = vsmall
            return dict([(u, float(c) / maxscore) for (u, c) in scores.items()])

    def separatewords(self, text):
        splitter = re.compile('\\W*')
        return [s.lower() for s in splitter.split(text) if s != '']

    def geometricDesign(self):
        self.title.grid(row=0,column=0,columnspan=5,sticky=N)
        self.url.grid(row=1,column=0)
        self.entry.grid(row=1,column=1,columnspan=2)
        self.build.grid(row=1,column=3,sticky=W)
        self.keyword.grid(row=2,column=0,columnspan=4,pady=5,ipady=3)
        self.search.grid(row=2,column=4)
        self.ranking.grid(row=3,column=0,ipady=5)
        self.weight.grid(row=3,column=1,sticky=W)
        self.filter.grid(row=3,column=2,sticky=W)
        self.word.grid(row=4,column=0)
        self.citation1.grid(row=5,column=0)
        self.wordweight.grid(row=4,column=1,sticky=W)
        self.citationweight.grid(row=5,column=1,sticky=W)
        self.papers.grid(row=4,column=2,rowspan=3,columnspan=2,sticky=W)

        self.scrollbar.grid(row=0,column=1,sticky=NS)
        self.text.grid(row=1,column=0,pady=10,padx=(25,0))
        self.previous.grid(row=0,column=1)
        self.pagenumber.grid(row=0,column=2,padx=5)
        self.next_.grid(row=0,column=3,padx=5)
        self.page.grid(row=0,column=0)


        self.frame1.grid()
        self.frame2.grid(sticky=W)
        self.frame3.grid()


def main():
    root = Tk()
    root.title("SEHIR Scholar")
    # root.geometry("850x500+150+100")
    app = ProjectAnalyzer(root)
    root.mainloop()


if __name__ == '__main__':
    main()

