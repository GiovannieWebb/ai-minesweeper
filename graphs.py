import csv
import matplotlib.pyplot as plt


def get_stats_from_csv(filename):
    """
    Returns a dictionary where keys are strings "iterations", "times", and 
    "result" and key values are corresponding lists. 
    """
    file = open(filename, mode="r", encoding='utf-8-sig')
    csvreader = csv.reader(file)
    headers = next(csvreader)
    iteration_column = []
    time_column = []
    result_column = []
    for row in csvreader:
        iteration_column.append(int(row[0]))
        time_column.append(float(row[1]))
        result_column.append(row[2])
    return {
        "iterations": iteration_column,
        "times": time_column,
        "results": result_column
    }


def calculate_num_wins():
    """
    Returns a dictionary with keys "easy", "medium", and "hard" where key 
    values are the number of wins.
    """
    wins_dict = {"easy": 0, "medium": 0, "hard": 0}

    easy_stats = get_stats_from_csv("data/easy-stats.csv")
    for result in easy_stats["results"]:
        if result == "W":
            wins_dict["easy"] += 1

    medium_stats = get_stats_from_csv("data/medium-stats.csv")
    for result in medium_stats["results"]:
        if result == "W":
            wins_dict["medium"] += 1

    hard_stats = get_stats_from_csv("data/hard-stats.csv")
    for result in hard_stats["results"]:
        if result == "W":
            wins_dict["hard"] += 1

    return wins_dict


def create_num_wins_bar_charts():
    """
    Creates bar charts where the x axis is the difficulty level and the y-axis
    is the number of wins.
    """
    difficulties = ["Easy", "Medium", "Hard"]
    wins = calculate_num_wins()
    wins_lst = []
    wins_lst.append(wins["easy"])
    wins_lst.append(wins["medium"])
    wins_lst.append(wins["hard"])

    plt.ylim((0, 50))
    plt.bar(difficulties, wins_lst)
    plt.title('Number of Wins After 50 Iterations')
    plt.xlabel('Difficulty')
    plt.ylabel('Number of Wins')
    plt.savefig('charts/wins')
    plt.show()


def calculate_average_times():
    """
    Returns a dictionary with keys "easy", "medium", and "hard" where key values 
    are the average time spent out of the number of corresponding games won.
    """
    num_wins = calculate_num_wins()
    easy_wins = num_wins["easy"]
    medium_wins = num_wins["medium"]
    hard_wins = num_wins["hard"]

    easy_stats = get_stats_from_csv("data/easy-stats.csv")
    easy_times = easy_stats["times"]
    easy_results = easy_stats["results"]
    easy_total_time = 0
    for i in range(len(easy_times)):
        if easy_results[i] == "W":
            easy_total_time += easy_times[i]

    medium_stats = get_stats_from_csv("data/medium-stats.csv")
    medium_times = medium_stats["times"]
    medium_results = medium_stats["results"]
    medium_total_time = 0
    for j in range(len(medium_times)):
        if medium_results[j] == "W":
            medium_total_time += medium_times[j]

    hard_stats = get_stats_from_csv("data/hard-stats.csv")
    hard_times = hard_stats["times"]
    hard_results = hard_stats["results"]
    hard_total_time = 0
    for k in range(len(hard_times)):
        if hard_results[k] == "W":
            hard_total_time += hard_times[k]

    return {
        "easy": easy_total_time / easy_wins,
        "medium": medium_total_time / medium_wins,
        "hard": hard_total_time / hard_wins
    }


def calculate_success_rates():
    """
    Returns a dictionary with keys "easy", "medium", and "hard" where key values 
    are the win success rate ((# wins / total iterations) * 100).
    """
    num_wins = calculate_num_wins()
    easy_wins = num_wins["easy"]
    medium_wins = num_wins["medium"]
    hard_wins = num_wins["hard"]

    easy_stats = get_stats_from_csv("data/easy-stats.csv")
    num_easy_iterations = len(easy_stats["results"])

    medium_stats = get_stats_from_csv("data/medium-stats.csv")
    num_medium_iterations = len(medium_stats["results"])

    hard_stats = get_stats_from_csv("data/hard-stats.csv")
    num_hard_iterations = len(hard_stats["results"])

    return {
        "easy": (easy_wins / num_easy_iterations) * 100,
        "medium": (medium_wins / num_medium_iterations) * 100,
        "hard": (hard_wins / num_hard_iterations) * 100
    }


if __name__ == '__main__':
    create_num_wins_bar_charts()
    # average_times = calculate_average_times()
    # print(average_times)
    # succes_rates = calculate_success_rates()
    # print(succes_rates)
