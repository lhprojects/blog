
import pickle
import numpy as np

class WikiTitles:

    def __init__(self, file):
            
        with open(file, "rb") as f:
            page_titles, redirect_map = pickle.load(f)

        page_title_indices = {}
        for i, page_title in enumerate(page_titles):
            page_title_indices[page_title] = i

        self.page_titles = page_titles
        self.redirect_map = redirect_map
        self.page_title_indices = page_title_indices
        
    def get_title_from_index(self, index):
        if index is not None and index >= 0:
            return self.page_titles[index]
    
    def get_index_from_title(self, title):
        page_title_indices = self.page_title_indices
        redirect_map = self.redirect_map

        iters = 0
        while True:
            if title in page_title_indices:
                return page_title_indices[title]

            # don't use capitalize, it we lower the first char of a name
            ctitle = title[:1].upper() + title[1:]
            if ctitle != title:
                if ctitle in page_title_indices:
                    return page_title_indices[ctitle]

            if title in redirect_map:
                title_ = redirect_map[title]
                # this is not a full dection of loop, but it's work
                if title_ == title or title_ == ctitle:
                    break
                title = title_
            elif ctitle in redirect_map:
                title_ = redirect_map[ctitle]
                if title_ == title or title_ == ctitle:
                    break
                title = title_
            else:
                break

            iters += 1
            if iters >= 5:
                break
