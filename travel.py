from math import sin, cos, sqrt, atan2, radians
import pandas as pd
import datetime

WEEK_DAYS = ['sat', 'sun', 'mon', 'tue', 'wed', 'thu', 'fri']  # used for days checking

##############################
class Flight: 
    '''Class to hold flights data'''
    def __init__(self, flight_num, source, destination, deprature, arrival, day):
        self.flight_num  = flight_num
        self.source      = source
        self.destination = destination
        self.deprature   = deprature
        self.arrival     = arrival
        self.day         = day
        self.arrival_day = self.day

    def __str__(self):  # to return flight data in print() statements
        return f'take flight {self.flight_num} from {self.source} to {self.destination}. Departure time {self.deprature} at ({self.day}) and arrival time {self.arrival} at ({self.arrival_day}).'

##############################
class Node:
    '''Node class for A* star search'''
    def __init__(self, city, parent=None):
        self.f = 0
        self.g = 0
        self.h = 0

        self.city   = city
        self.parent = parent
        self.path   = []  # path of flights until the goal
        if self.parent: # append path of parent to its child
            for flight in self.parent.path:
                self.path.append(flight)

    def __eq__(self, other):  # used in comparisons between 2 nodes
        return self.city.lower() == other.city.lower()

##############################
# read each excel sheet individually 
# df1 contains flights data
# df2 contains cities data
xlsx = pd.ExcelFile('Travel Agent.xlsx')
df1 = pd.read_excel(xlsx, 'Flights')
df2 = pd.read_excel(xlsx, 'Cities')

# convert DataFrames to lists to be used in searching
flights = []
for index, row in df1.iterrows():
    for day in row['List of Days'][1:-1].split(', '):
        flight = Flight(row['Flight Number'], row['Source'], row['Destination'], 
            row['Departure Time'], row['Arrival Time'], day)
        flights.append(flight)
cities = df2.values.tolist()

##############################
def get_heuristic(dest_city, goal):
    '''Return the time taken by plane from specific city to user's goal in seconds (i.e heuristic)'''
    R = 6373.0  # radius of earth in km

    for city in cities:
        if city[0].lower() == dest_city.lower():
            lat1 = radians(city[1])
            lon1 = radians(city[2])
        if city[0].lower() == goal.lower():
            lat2 = radians(city[1])
            lon2 = radians(city[2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    
    # 900/hr is the estimated speed of the plane
    # the time taken by the plane in hrs multiplied by 3600 to be converted to secs 
    return (distance / 900) * 3600 

##############################
def get_allowed_child_cities(city, days_range, prev_arrival_day, prev_arrival_time):
    '''Return cities which can be reached from current given city at the days and time range'''
    dest_cities = []

    for flight in flights:
        # check if flight's source equals current city, flight's day is in range
        # and the flight's day after the previous arrival day
        # or at the same day with flight's deprature after previous arrival time
        if flight.source.lower() == city.lower() and flight.day in days_range and (WEEK_DAYS.index(flight.day) > WEEK_DAYS.index(prev_arrival_day) or flight.deprature > prev_arrival_time):
            # if the flight arrives at the next day, then change the arrival day to the next
            if flight.arrival < flight.deprature:  
                day_idx = WEEK_DAYS.index(flight.day)
                flight.arrival_day = WEEK_DAYS[day_idx + 1] if day_idx != 6 else WEEK_DAYS[0]
            dest_cities.append(flight)  # append the flight to the childs of current city

    return dest_cities

##############################
def get_time_difference(time1, time2):
    '''Return difference between 2 times in seconds => (time2 - time1)'''
    diff = datetime.datetime.combine(datetime.date.min, time2) - datetime.datetime.combine(datetime.date.min, time1)
    return diff.total_seconds()

##############################
def a_star(start, goal, days_range):
    '''A* pathfinding finding algorithm for flights travel agent'''
    start_node = Node(start)
    goal_node = Node(goal)

    # lists to track the nodes and which one to choose
    open_list = []
    closed_list = []

    # begin with start node added to open list
    open_list.append(start_node)

    while open_list:  # while open list contain nodes
        # find the smallest F in open list
        curr_node = open_list[0]
        curr_idx = 0
        for idx, city in enumerate(open_list):
            if city.f < curr_node.f:
                curr_node = city
                curr_idx = idx

        # pop current city from open list, add it to closed list
        open_list.pop(curr_idx)
        closed_list.append(curr_node)

        # if the goal is reached, then return it
        if curr_node == goal_node:
            return curr_node

        # these three variables are used to get the child nodes
        # firstly they are initialized with data of the start city
        city = start  
        time = datetime.time(0,0,0)
        day = days_range[0]
        # if the current city isn't equal the start city
        # then get the data of the last flight at the path
        if curr_node != start_node:
            last_flight = curr_node.path[-1]
            city = last_flight.destination
            time = last_flight.arrival
            day = last_flight.day

        # get all the flights that i can make from current city (i.e Child or Neighbour nodes)
        childs = get_allowed_child_cities(city, days_range, day, time)

        # foreach flight from the current city to its childs
        for flight in childs:  
            child = Node(flight.destination, curr_node)  # child node with destination city & current parent
            child.path.append(flight)  # add the flight to the path of the current child

            # If child is in the closed list (i.e visited before)
            if child in closed_list:
                continue

            # calculate the waiting time between previous arrival and current flight's deprature
            waiting_time = 0
            if child.parent != start_node:  # if the child's parent isn't the start city 
                # if the flight's day is after the previous arrival day
                # then will create two dates to get the difference between days in seconds
                if WEEK_DAYS.index(flight.day) > WEEK_DAYS.index(day):
                    # create a temporary date with the previous arrival time
                    prev_flight = datetime.datetime(1,1,1, time.hour, time.minute, 0)
                    # add the days difference to the temporary date to get current flight date
                    curr_flight = prev_flight + datetime.timedelta(WEEK_DAYS.index(flight.day) - WEEK_DAYS.index(day))
                    # change the time of the current date to the actual flight's time
                    curr_flight.replace(hour=flight.deprature.hour, minute=flight.deprature.minute)
                    waiting_time = (curr_flight - prev_flight).total_seconds()  
                else:  # if deprature and previous arrival at the same day
                    waiting_time = get_time_difference(time, flight.deprature)
            
            # calculate the flight's duration from deprature to arrival
            flight_duration = 0
            if flight.arrival < flight.deprature:  # plane arrived at the next day
                diff1 = get_time_difference(flight.deprature, datetime.time(23,59,59))
                diff2 = get_time_difference(datetime.time(00,00,00), flight.arrival)
                flight_duration  = diff1 + diff2
            else:  # plane arrived at the same day
                flight_duration = get_time_difference(flight.deprature, flight.arrival)
            
            # calculate child's cost, heuristic and total cost
            child.g = curr_node.g + waiting_time + flight_duration
            child.h = get_heuristic(flight.destination, goal)
            child.f = child.g + child.h

            # If child is in the open list and its (F) is greater than the existing one
            if len([open_node for open_node in open_list if child == open_node and child.f > open_node.f]) > 0:
                continue

            open_list.append(child)  # add child to the open list

    # Return None, if no path is found
    return None

##############################         
def travel_agent(src, dest, days):
    '''Take user input and process it to work on A* search'''
    week_days = ("Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
    user_days_range = []
    
    # Change the name of the day to its abbreviation, ex: Sunday ==> sun
    # and create the list of days in the range of two days given by user
    for i, day in enumerate(week_days):
        if day.lower() == days[0].lower():
            for j in range(i, len(week_days)):
                user_days_range.append(WEEK_DAYS[j])
                if week_days[j] == days[-1]:
                    break

    goal = a_star(src.lower(), dest.lower(), user_days_range)
    
    # if the goal isn't reached at the user's days range add a day
    # to the range each time until reach the end of the week (i.e Friday)
    while goal is None:
        if user_days_range[-1] == 'fri':
            break
        user_days_range.append(WEEK_DAYS[WEEK_DAYS.index(user_days_range[-1]) + 1])
        print(f'* No flights at your range from ({src}) to ({dest}),')
        print(f'day ({WEEK_DAYS[WEEK_DAYS.index(user_days_range[-1])]}) added to it, your new range is: {user_days_range}.')
        goal = a_star(src.lower(), dest.lower(), user_days_range)
        
    return (goal, src, dest)  # return goal node, source city, destination city 

##############################
def print_solution(agent):
    '''Print the results of the search problem'''
    result, src, dest = agent
    if result is None:
        print(f'=> Unfortunately, No flights between ({src}) and ({dest}), or may you entered not-valid cities !')
    else:
        print(f'=> The best route in your days range from ({src}) to ({dest}):')
        for i, flight in enumerate(result.path):
            print(f'Step {i + 1}:', flight)
    print('----------------------------------------')

##############################
# some test cases for our travel agent
print_solution(travel_agent('Cairo', 'San Francisco', ['Tuesday', 'Wednesday']))
print_solution(travel_agent('Edinburgh', 'Aswan', ['Monday','Thursday']))
print_solution(travel_agent('San Francisco', 'New York', ['Saturday', 'Monday']))
print_solution(travel_agent('Aswan', 'Cairo', ['Thursday','Friday']))
print_solution(travel_agent('Giza', 'New York', ['Sunday','Wednesday']))
