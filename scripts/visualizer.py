"""
シミュレーション結果を可視化するためのクラス
"""
from pprint import pprint
from typing import List
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter


class LogVisualizer(object):
    def __init__(self, logs: List[dict]) -> None:
        # ex.)
        # logs = [{
        # 	date: [],
        # 	st_total_value: [],
        # 	jct_total_value: [],
        # 	jct_portfolio: [],
        # 	necessary_collateral_value: [],
        # 	collateral_portfolio: []
        # }]
        self.logs = logs
        self.date_list = logs['date']
        self.collateral_portfolio_list = logs['collateral_portfolio']
        self.collateral_sum_list = [self.portfolio_sum(log) for log in self.collateral_portfolio_list]
        self.necessary_collateral_value_list = logs['necessary_collateral_value']
        self.jct_portfolio_list = logs['jct_portfolio']
        self.initial_collateral_portfolio_list = logs['initial_collateral_portfolio']
        self.initial_collateral_value_list = [self.portfolio_sum(portfolio) for portfolio in self.initial_collateral_portfolio_list]
        self.additional_issue_list = logs['additional_issue']
        print('Log Visualizer initialized.')
        pprint(logs)

    @staticmethod
    def portfolio_sum(portfolio: dict) -> int:
        total_value = 0
        for security in portfolio.values():
            total_value += security['num'] * security['price']
        return total_value

    def compare_collateral_portfolio(self) -> None:
        # 初期差し入れ担保、価格調整自動化後差し入れ担保の価値推移比較
        _fig, ax1 = plt.subplots(figsize=(30, 15))
        ax1_2 = ax1.twinx()

        plt.title('自動調整前後の差し入れ担保の価値変動比較', fontsize=30, pad=20, fontname="Hiragino Sans")
        ax1.plot(self.date_list, self.initial_collateral_value_list, marker='o', markersize=5, color='red', label='Initial Collateral Portfolio Value')
        ax1.set_ylabel('Initial Collateral Portfolio Value', fontsize=20, fontname="Hiragino Sans")
        ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax1_2.plot(self.date_list, self.necessary_collateral_value_list, marker='o', markersize=5, color='blue', label='Adjusted Collateral Value')
        ax1_2.set_ylabel('Adjusted Collateral Value', fontsize=20, fontname="Hiragino Sans")
        ax1_2.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax1.set_ylim(ax1_2.get_ylim())
        handler1, label1 = ax1.get_legend_handles_labels()
        handler2, label2 = ax1_2.get_legend_handles_labels()

        ax1.legend(handler1 + handler2, label1 + label2, loc=2, borderaxespad=0., fontsize=20)
        ax1.tick_params(axis='y', colors='red', labelsize=15)
        ax1.yaxis.offsetText.set_fontsize(15)
        ax1.xaxis.offsetText.set_fontsize(15)
        ax1_2.xaxis.offsetText.set_fontsize(15)
        ax1_2.tick_params(axis='y', colors='blue', labelsize=15)
        ax1_2.yaxis.offsetText.set_fontsize(15)

    def calc_collateral_percentage(self) -> None:
        # 差し入れている担保の割合の推移
        color_list = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
        security_list = self.initial_collateral_portfolio_list[0].keys()
        collateral_percentages = {}
        for security in security_list:
            collateral_percentages[security] = []
            for portfolio in self.collateral_portfolio_list:
                if security in portfolio:
                    collateral_percentages[security].append(portfolio[security]['num'] / self.initial_collateral_portfolio_list[0][security]['num'])
                else:
                    collateral_percentages[security].append(0)

        plt.figure(figsize=(30, 15))
        plt.title("差し入れ担保の割合推移", fontsize=30, pad=20, fontname="Hiragino Sans")
        for idx, security in enumerate(security_list):
            plt.plot(self.date_list, collateral_percentages[security], marker='o', markersize=5, color=color_list[idx], label=security)
        plt.legend(loc=2, fontsize=20)

        date_additional_issue = []
        for i, x in enumerate(self.additional_issue_list):
            if x:
                date_additional_issue.append(self.date_list[i])
        plt.vlines(date_additional_issue, ymin=0.5, ymax=1.5, color='orange', linestyle='dashed', linewidth=3)
        return collateral_percentages
