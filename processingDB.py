import mysql.connector
from configparser import ConfigParser
from os import popen, getcwd
import time

data_base = {}
array_PID = []
array_PID_db = []
name_table = ''

time_sleep = {
    'test': 2,
    'one_minute': 60,
    'two_minutes': 120,
    'three_minutes': 180
}


def gen_element(USER, PID, PPID, C, SZ, RSS, PSR, TTY, TIME, CMD, PCPU, PMEM, LIVE = '1'):
    time_process = time.time()
    dicti = {
        'USER': USER,
        'PID': PID,
        'PPID': PPID,
        'C': C,
        'SZ': SZ,
        'RSS': RSS,
        'PSR': PSR,
        'STIME': time_process,
        'TTY': TTY,
        'TIME': TIME,
        'CMD': CMD,
        'CPU': float(PCPU),
        'MEM': float(PMEM),
        'GPU': '',
        'GMEM': '',
        'ENDTIME': time_process,
        'LIVE': LIVE
    }
    return dicti


def read_db_config(filename, section='mysql'):
    # create parser and read ini configuration file
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to mysql
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))

    return db


def update_by_pid(PID, CPU, MEM, GPU, GMEM):
    try:
        connect = mysql.connector.connect(host=data_base.get('host'),
                                          database=data_base.get('database'),
                                          user=data_base.get('user'),
                                          password=data_base.get('password'))

        cursor = connect.cursor()
        update_row = 'UPDATE ' + name_table + ' SET CPU = %s, MEM = %s, ENDTIME = %s, LIVE = "1",' \
                                              ' GPU = %s, GMEM = %s WHERE PID = %s'
        cursor.execute(update_row, (CPU, MEM, time.time(), GPU, GMEM, PID,))

        connect.commit()

    except mysql.connector.Error as e:
        print(e)

    finally:
        cursor.close()
        connect.close()


def update_by_pid_death(PID):
    try:
        connect = mysql.connector.connect(host=data_base.get('host'),
                                          database=data_base.get('database'),
                                          user=data_base.get('user'),
                                          password=data_base.get('password'))

        cursor = connect.cursor()
        update_row = 'UPDATE ' + name_table + ' SET LIVE = %s WHERE PID = %s'
        cursor.execute(update_row, ('0', PID,))

        connect.commit()

    except mysql.connector.Error as e:
        print(e)

    finally:
        cursor.close()
        connect.close()


def read_db():
    json_db = []
    array_PID_db.clear()

    try:
        dbconfig = read_db_config(path_to_config)
        connect = mysql.connector.connect(host=data_base.get('host'),
                                          database=data_base.get('database'),
                                          user=data_base.get('user'),
                                          password=data_base.get('password'))
        cursor = connect.cursor()
        read_row = "SELECT * FROM " + name_table + " WHERE LIVE = '1'"
        cursor.execute(read_row)

        row = cursor.fetchone()

        while row is not None:
            # print(row)  USER, PID, PPID, C, SZ, RSS, PSR, STIME, TTY, TIME, CMD, PCPU, PMEM, ENDTIME, LIVE
            #               0   1   2     3   4   5     6     7     8    9    10    11    12    13      14
            json_db.append(gen_element(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[8], row[9], row[10],
                                       row[11], row[12], row[14]))
            array_PID_db.append(row[1])
            row = cursor.fetchone()

    except mysql.connector.Error as e:
        print(e)

    finally:
        cursor.close()
        connect.close()

    return json_db

def get_njson():	
    row = ''
    command = 'nvidia-smi pmon -c 1 -s m'
    output = popen(command)
    process = output.read()
    output.close()

    row = process.split('\n')

    # row = ''
    # with open('nvidiaData', 'r') as file:
    #       row = file.read()
    # output = popen('nvidia-smi pmon -c 1 -s m')
    # row = output.read()
    # output.close()

    # row = row.split('\n')

    row.pop(0)
    row.pop(0)


    for i in range(len(row)):
        row[i] = row[i].split(' ')

    for i in range(len(row)):
        for j in range(row[i].count('')):
            row[i].remove('')

    array_json = []
    for i in range(len(row) - 1):
        if row[i][0] != 'root':
            array_json.append({
                'GPU': row[i][0],
                'PID': row[i][1],
                'TYPE': row[i][2],
                'GMEM': row[i][3],
                'COMMAND': row[i][4]
            })
    return array_json


def get_json():
    array_PID.clear()
    command = 'ps -eo user,pid,ppid,c,sz,rss,psr,tty,time,pcpu,pmem,cmd'
    output = popen(command)
    process = output.read()
    output.close()

    process = process.split('\n')

    for i in range(len(process)):
        process[i] = process[i].split(' ')

    for i in range(len(process)):
        for j in range(process[i].count('')):
            process[i].remove('')

    array_json = []
    process = process[1:]
    for i in range(len(process) - 1):
        if process[i][11] != 'ps' and process[i][11] != '/usr/bin/ps':
            cmd_row = ''
            for cmd_element in range(11, len(process[i])):
                cmd_row += process[i][cmd_element]
            if cmd_row != '/bin/sh-cps-eouser,pid,ppid,c,sz,rss,psr,tty,time,pcpu,pmem,cmd':
                array_json.append(gen_element(process[i][0], process[i][1], process[i][2], process[i][3],
                                          process[i][4], process[i][5], process[i][6], process[i][7],
                                          process[i][8], cmd_row, process[i][9], process[i][10]))
                array_PID.append(int(process[i][1]))

    array_njson = get_njson()
    for element in array_json:
        for element_n in array_njson:
            if element.get('PID') == element_n.get('PID'):
                element.update({'GPU': str(element.get('GPU')) + '|' + element_n.get('GPU')})
                element.update({'GMEM': str(element.get('GMEM')) + '|' + element_n.get('GMEM')})
                element.update({'TYPE_': element_n.get('TYPE')})

    return array_json


def add_data(cell):
    try:
        query = 'INSERT INTO ' + name_table + '(USER, PID, PPID, C, SZ, RSS, PSR, STIME, TTY, TIME, CMD, CPU, MEM, GPU, TYPE_, GMEM, ENDTIME, LIVE) ' \
                                              'VALUES(%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

        connect = mysql.connector.connect(host=data_base.get('host'),
                                          database=data_base.get('database'),
                                          user=data_base.get('user'),
                                          password=data_base.get('password'))

        cursor = connect.cursor()
        args = (cell.get('USER'), cell.get('PID'), cell.get('PPID'), cell.get('C'),
                cell.get('SZ'), cell.get('RSS'), cell.get('PSR'), cell.get('STIME'), cell.get('TTY'),
                cell.get('TIME'), cell.get('CMD'), cell.get('CPU'), cell.get('MEM'), cell.get('GPU'),
                cell.get('TYPE_'), cell.get('GMEM'), cell.get('ENDTIME'), cell.get('LIVE'))

        cursor.execute(query, args)

        # if cursor.lastrowid:
        #     print('last insert id', cursor.lastrowid)
        # else:
        #     print('last insert id not found')

        connect.commit()

    except mysql.connector.Error as error:
        print(error)

    finally:
        cursor.close()
        connect.close()


def processing(json, json_db, number_of_polls):
    len_json = len(json) # Json in pc
    len_json_db = len(json_db) # Json in db

    for index in range(len_json if len_json > len_json_db else len_json_db):
        if index < len_json_db:
            if json_db[index].get('PID') in array_PID: #and json_db[index].get('ENDTIME') == None:
                #number element in array for get value CPU and MEM
                number_in_array = array_PID.index(json_db[index].get('PID'))
                congestion_CPU = (json_db[index].get('CPU') * number_of_polls + (json[number_in_array].get('CPU') if json[number_in_array].get('CPU') > json_db[index].get('CPU') else json_db[index].get('CPU'))) / (number_of_polls + 1)
                # print('PID ' + str(json_db[index].get('PID')),
                #       '\ncongestion CPU ' + str(congestion_CPU),
                #       '\nnumber_iteration ' + str(number_of_polls),
                #       '\nvalue in db ' + str(json_db[index].get('CPU')),
                #       '\nvalue in pc ' + str(json[number_in_array].get('CPU')))
                if json_db[index].get('CPU') == json[number_in_array].get('CPU') == 0:
                    congestion_CPU = 0
                update_by_pid(json_db[index].get('PID'), congestion_CPU,
                              json[number_in_array].get('MEM') if json[number_in_array].get('MEM') > json_db[index].get('MEM') else json_db[index].get('MEM'),
                              json[number_in_array].get('GPU'), json[number_in_array].get('GMEM'))

            else:
                update_by_pid_death(json_db[index].get('PID'))
        if index < len_json:
            if int(json[index].get('PID')) not in array_PID_db:
                # print('add: ', json[index].get('PID'), ' ', json[index])
                add_data(json[index])
            # else:
            #     update_by_pid_death(json_db[index].get('PID'))
    number_of_polls += 1
    # except IndexError as e:
    #     print(e)
    #     print(error_index)





if __name__ == '__main__':
    path_to_config = getcwd() + '/config.ini'
    try:
        data_base = read_db_config(path_to_config)
        name_table = data_base.get('last_name_table')
        number_of_polls = 1
        while True:
            connect = mysql.connector.connect(host=data_base.get('host'),
                                          database=data_base.get('database'),
                                          user=data_base.get('user'),
                                          password=data_base.get('password'))
            connect.close()
            processing(get_json(), read_db(), number_of_polls)
            #time.sleep(time_sleep.get('test'))

    except KeyboardInterrupt as er:
        pass
    except mysql.connector.errors.DatabaseError as error:

        for connection_attempt in range(3):
            # print(error, '\n', 'Connection attempt. Number attempt: ' + str(connection_attempt))
            try:
                connect = mysql.connector.connect(host=data_base.get('host'),
                                                  database=data_base.get('database'),
                                                  user=data_base.get('user'),
                                                  password=data_base.get('password'))
                cursor = connect.cursor()
                cursor.execute('SHOW TABLES')

                row = cursor.fetchall()
                table_list = []
                for name_table_check in row:
                    table_list.append(name_table_check[0])
                if name_table not in table_list:
                    command = 'python3 /usr/local/bin/tmon/createDataBase.py'
                    popen(command)
                # print('Connection detected')
                cursor.close()
                connect.close()
                break

            except mysql.connector.errors.DatabaseError:
                pass
