
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import requests
import logging
import re
import os

def main():    
    #logging file
    logging.basicConfig(filename='test.log', level = logging.DEBUG,
                        format='%(message)s')
    logging.debug('start')

    current_results_url = 'https://ccsportscarclub.org/autocross/schedule/'
    page = requests.get(current_results_url)
    soup = BeautifulSoup(page.text, 'html.parser')

    #get a list of all links on the web page    
    url_fulltag_list = soup.find_all('a')

    #creating a list of urls which contains files or msreg
    #these urls will be the only ones we need to look through    
    url_notag_list = delete_tags(url_fulltag_list) 
    
    #writing to files
    location = ''
    length = len(url_notag_list)
    for i in range(length):
        #gets raw data
        if url_notag_list[i].find('_raw') != -1:            
            write_to_files(9,location, url_notag_list[i])

        #gets pax data           
        if url_notag_list[i].find('_pax') != -1:            
            write_to_files(11,location, url_notag_list[i])

        #gets final data
        if url_notag_list[i].find('_fin') != -1:
            if url_notag_list[i].lower().find('-pro') == -1:                
                write_to_file_fin(location, url_notag_list[i])
            

        #gets location
        if url_notag_list[i].find('msreg') != -1:
            if (length - i) > 1:            
                new_page = requests.get(url_notag_list[i])
                new_soup = BeautifulSoup(new_page.text, 'html.parser')
                location = new_soup.find('div',{'class':'section__description section__description_s'}).text
                

    # start reading in files to prepare to compare
    dir_list = os.listdir(path='files/')
    indexx = 0
    dir_length = len(dir_list)
    my_file2 = open('output2.txt','w')
    while indexx < dir_length:
        curr_path = dir_list[indexx]
        k_index = indexx + 1
        # Full path = cone-slayer-saturday-04-23-2022_pax.txt
        #sub_path = cone-slayer-saturday-04-23-2022
        #gets the sub path
        split_list = re.split('_pax|_raw|_fin', curr_path)
        sub_path = split_list[0]        
        #holds the paths associated with curr_path
        #by matching with sub_path
        filePathList = []
        #holds the index of the last file found k
        k_holder = 0

        while k_index < dir_length:
            if dir_list[k_index].find(sub_path) != -1:
                filePathList.append(dir_list[k_index])
                k_holder = k_index
            k_index += 1
        if k_holder == 0:
            indexx+=1
        else:
            indexx = k_holder +1

        raw_path = ""
        pax_path = ""
        fin_path = ""
        filePathList.append(curr_path)
        for path in filePathList:
            if path.find('_raw') != -1:
                raw_path = path
            if path.find('_pax') != -1:
                pax_path = path
            if path.find('_fin') != -1:
                fin_path = path
               
        raw_data_list = read_files(raw_path)        
        pax_data_list = read_files(pax_path)        
        fin_data_list = read_files(fin_path)        
        
        total_data = []
        total_data.append(raw_data_list[0]) #location
        total_data.append(raw_data_list[1]) #date
        total_data.append(raw_data_list[2]) #event name        
        logging.debug(raw_data_list[2])

        #Start comparing files
        #name index 4 for pax
        #name index 4 for raw
        #name index 3 for fin        
        for index in range(3,len(raw_data_list)):
            #logging.debug(index)
            raw_name = raw_data_list[index][4].lower()
            ratio_limit = 90
            pindex = 3
            pax_index_holder = -1
            fin_index_holder = -1
            findex = 3
            logging.debug('Finding pindex Holder')
            while pindex < len(pax_data_list):
                pax_name = pax_data_list[pindex][4].lower()
                ratio = fuzz.ratio(raw_name,pax_name)
                if ratio > ratio_limit:
                    #found a match
                    pax_index_holder = pindex
                    pindex= len(pax_data_list)+1
                else:
                    #reduce ratio limit to help find a match if it has checked the entire array
                    if pindex == len(pax_data_list) -1:
                        pindex = 3
                        ratio_limit = ratio_limit -1
                pindex+=1
            fin_ratio_limit = 90
            logging.debug('finding fin index holder')
            while findex < len(fin_data_list):
                fin_name = fin_data_list[findex][3].lower()
                ratio = fuzz.ratio(raw_name,fin_name)
                if ratio > fin_ratio_limit:
                    #found a match
                    fin_index_holder = findex
                    findex= len(fin_data_list)+1
                else:
                    #reduce ratio limit to help find a match if it has checked the entire array
                    if findex == len(fin_data_list) -1:
                        findex = 3
                        fin_ratio_limit = fin_ratio_limit -1
                findex+=1
            logging.debug("fin FOund")
            #EventData
            #Run Data
            class_name = raw_data_list[index][2]
            car_num = raw_data_list[index][3]
            driver_name = raw_data_list[index][4]
            car_model = raw_data_list[index][5]
            raw_time = raw_data_list[index][6]
            event_id = "EventID"
            cones_hit = 0
            #Best Run Data
            run_id = "RunID"
            raw_class_position = raw_data_list[index][1]
            pax_class_position = pax_data_list[pax_index_holder][1]
            pax_time = pax_data_list[pax_index_holder][8]
            note_id = "NoteID"

            cones_hit_event = 0
            total_time = 0
            #vars to get three run avg
            run_count = 1
            dnf = False
            three_run_sum = 0
            three_run_avg = "N/A"
            #getting cones hit for best run, cones hit total for event, and three run avg               
            if is_float(raw_time) == True and fin_index_holder != -1:
                fin_run_list = fin_data_list[fin_index_holder][6:-2]
                for time in fin_run_list:
                    timesplit = time.split('+')
                    #if arr > 1,  checks for how many cones are hit or DNF, 
                    # adds cone penalty time to total time, 2 secs. 
                    if len(timesplit) > 1:
                        if timesplit[1].isdigit():
                            cones_hit_event += int(timesplit[1])
                            if is_float(timesplit[0]):
                                total_time = float(timesplit[0]) + (float(timesplit[1])*2)
                        else:
                            if is_float(timesplit[0]):
                                total_time = float(timesplit[0])
                    else:
                        if is_float(timesplit[0]):
                            total_time = float(timesplit[0])
                    ##matching the raw time to get the cones hit for that run only
                    if total_time == float(raw_time):
                        if len(timesplit) > 1:
                            if timesplit[1].isdigit():
                                cones_hit = int(timesplit[1])
                    #get the first 3 run average
                    #if a run contians DNF, avg = DNF
                    if run_count <=3:
                        if len(timesplit) > 1:
                            if timesplit[1] == 'DNF':
                                dnf = True
                        if is_float(timesplit[0]):
                            three_run_sum+= float(timesplit[0])
                        else:
                            dnf = True
                        run_count+=1
                if dnf == True:
                    three_run_avg = 'DNF'
                else:
                    if run_count == 4:
                        three_run_avg = str(round(three_run_sum/3,3))
            if fin_index_holder != -1:
                fin_name = fin_data_list[fin_index_holder][3].lower()
            else:
                fin_name = "NoFinName"

            pax_name = pax_data_list[pax_index_holder][4].lower()
            row_list = [class_name, car_num, driver_name, car_model, raw_time, cones_hit,
                                        event_id, run_id, raw_class_position, pax_class_position,
                                        pax_time, note_id,three_run_avg,pax_name,fin_name]
            total_data.append(row_list)

        logging.debug('Writing to File for ^^^')
        for line in total_data:
            for word in line:
                my_file2.write(str(word) + '|')
            my_file2.write('\n')
        my_file2.write('--------------------------------------------------------------------------------\n')   
        #my_file2.close()
        #break
    my_file2.close()
    # end of while loop

def read_files(path):
    '''Reads file line by line, splits the string
    , returns a list of lists of stripped strings'''
    logging.debug(path)
    my_file = open('files/'+path,'r')
    lines = my_file.readlines()
    data_list =  []
    for line in lines:
        newLine = re.split(r"[\n|]", line)
        data_list.append(newLine)
    my_file.close()
    return data_list
    


def write_to_files(num_fields, location, url):
    '''Takes in the number of data fields, a location, and a URL
    /  writes table contents of url to files'''
    #get file name and open a file
    filename = get_filename(url).lower()
    my_file = open('files/'+filename+'.txt', 'w') 
    #soup it up
    new_page = requests.get(url)
    new_soup = BeautifulSoup(new_page.text, 'html.parser')

    #get event name
    event_name = ""
    f_list = filename.split('-')
    for word in f_list:
        if True in [char.isdigit() for char in word]:
            pass
        else:
            event_name += word+' '
    # get date Only works with 2022 results
    date= re.findall(r'\d+', filename)
    date = '-'.join(date)
       
    #find all table data
    td_find = new_soup.find_all('td')

    #writing to file intervals of num_fields 
    my_file.write(location.strip() + '\n') 
    my_file.write(date + '\n')
    my_file.write(event_name + '\n')   
    count = 1
    for td in td_find:
        if count % num_fields == 0:
            #td_list.append('\n')
            my_file.write(td.text+'|\n')
        else:
            my_file.write(td.text+'|')
        count += 1
    my_file.close()

def write_to_file_fin(location, url):
    '''Takes a location and url to write the final data'''
        #get file name and open a file
    filename = get_filename(url).lower()
    my_file = open('files/'+filename+'.txt', 'w') 
    #soup it up
    new_page = requests.get(url)
    new_soup = BeautifulSoup(new_page.text, 'html.parser')

    #get event name
    event_name = ""
    f_list = filename.split('-')
    for word in f_list:
        if True in [char.isdigit() for char in word]:
            pass
        else:
            event_name += word+' '
    # get date Only works with 2022 results
    date= re.findall(r'\d+', filename)
    date = '-'.join(date)

    my_file.write('Location\n')
    my_file.write('Date\n')
    my_file.write('Event\n')
    table_lists = new_soup.find_all('table')    
    tr_list = table_lists[2].find_all('tr')
    for tr in tr_list:
        td_list = tr.find_all('td')
        if len(td_list) > 0:
            for td in td_list:
                my_file.write(td.text+'|')
            my_file.write('\n')
    my_file.close()
        

def delete_tags(taglist):
    '''Takes a list of <a> tagged urls
   returns a non tagged list aka just the url
    '''
    no_taglist = []
    for urls in taglist:
        if urls['href'].find('files') != -1 or urls['href'].find('msreg') != -1:
            no_taglist.append(urls['href'])

    return no_taglist

def get_filename(url):
    '''Takes a url and extracts the filename'''
    split_list = url.split('/')
    a = split_list[-1]
    split_list = a.split('.')
    filename = split_list[0]
    return filename

def is_float(n):
    '''Determines if input n is a float'''
    try:
        float(n)
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    main()