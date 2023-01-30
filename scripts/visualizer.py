"""
シミュレーション結果を可視化するためのクラス
"""
from typing import List, Optional
import copy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import statistics


class LogVisualizer(object):
    def __init__(self, logs: List[dict], save_path: Optional[str] = None) -> None:
        # ex.)
        # logs = [{
        # 	date: [],
        # 	st_total_value: [],
        # 	jct_total_value: [],
        # 	jct_portfolio: [],
        # 	necessary_collateral_value: [],
        # 	collateral_portfolio: []
        #   collateral_sum: []
        #   borrower_additional_issue: []
        #   lender_additional_issue: []
        #   has_done_margincall: []
        # }]
        self.logs = logs
        self.date_list = logs['date']
        self.collateral_portfolio_list = logs['collateral_portfolio']
        self.collateral_sum_list = [self.portfolio_sum(log) for log in self.collateral_portfolio_list]
        self.necessary_collateral_value_list = logs['necessary_collateral_value']
        self.collateral_price_diff_list = self.calc_abs_price_diff(self.necessary_collateral_value_list, self.collateral_sum_list)
        self.jct_portfolio_list = logs['jct_portfolio']
        self.initial_collateral_portfolio_list = logs['initial_collateral_portfolio']
        self.initial_collateral_value_list = [self.portfolio_sum(portfolio) for portfolio in self.initial_collateral_portfolio_list]
        self.borrower_additional_issue_list = logs['borrower_additional_issue']
        self.lender_additional_issue_list = logs['lender_additional_issue']
        self.has_done_margincall_list = logs['has_done_margincall'] if 'has_done_margincall' in logs else []
        self.st_total_value_list = logs['st_total_value']

        if save_path:
            np.save(save_path, logs)
        print('Log Visualizer initialized.')

    @staticmethod
    def portfolio_sum(portfolio: dict) -> int:
        total_value = 0
        for security in portfolio.values():
            total_value += security['num'] * security['price']
        return total_value

    @staticmethod
    def calc_abs_price_diff(list_1: List[int], list_2: List[int]) -> List[int]:
        if len(list_1) != len(list_2):
            raise ValueError('length of 2 lists are not the same')
        price_diff_list = [abs(price_1 - list_2[idx]) for idx, price_1 in enumerate(list_1)]
        return price_diff_list

    def calc_price_diff_result(self) -> dict:
        # result = {
        #   max: 0
        #   min: 0
        #   mean: 0
        #   accumulation: 0
        # }
        result = {}
        result['raw_data'] = copy.deepcopy(self.collateral_price_diff_list)
        result['accumulation'] = sum(self.collateral_price_diff_list)
        result['mean'] = statistics.mean(self.collateral_price_diff_list)
        result['_mean'] = sum(self.collateral_price_diff_list) / len(self.collateral_price_diff_list)
        result['max'] = max(self.collateral_price_diff_list)
        result['min'] = min(self.collateral_price_diff_list)
        return result

    def compare_initial_collateral_portfolio(self) -> None:
        # 初期差し入れ担保、価格調整自動化後差し入れ担保の価値推移比較
        _fig, ax1 = plt.subplots(figsize=(30, 15))
        # ax1_2 = ax1.twinx()

        # plt.title('自動調整前後の差し入れ担保の価値変動比較', fontsize=30, pad=20, fontname="Hiragino Sans")
        ax1.plot(self.date_list, self.initial_collateral_value_list, marker='o', markersize=5, color='red', label='初期差し入れ担保資産価値')
        ax1.set_ylabel('総価値（円）', fontsize=24, fontname="Hiragino Sans")
        ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax1.plot(self.date_list, self.necessary_collateral_value_list, marker='o', markersize=5, color='blue', label='貸付資産価値')
        # ax1_2.set_ylabel('貸付資産', fontsize=20, fontname="Hiragino Sans")
        # ax1_2.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        # ax1_2.yaxis.offsetText.set_fontsize(20)
        # ax1_2.set_ylim(ax1.get_ylim())
        # handler1, label1 = ax1.get_legend_handles_labels()
        # handler2, label2 = ax1_2.get_legend_handles_labels()

        ax1.legend(loc=4, prop={"size": 24, "family": "Hiragino Sans"})
        ax1.tick_params(labelsize=24)

        ax1.xaxis.offsetText.set_fontsize(24)
        ax1.yaxis.offsetText.set_fontsize(24)
        # ax1_2.xaxis.offsetText.set_fontsize(24)
        # ax1_2.tick_params(axis='y', colors='blue', labelsize=24)
        # ax1_2.yaxis.offsetText.set_fontsize(15)

    def compare_initial_collateral_portfolio_ratio(self, ymin: float = -0.2) -> None:
        # 初期差し入れ担保、価格調整自動化後差し入れ担保の価値変動比推移比較
        _fig, ax1 = plt.subplots(figsize=(30, 15))

        init_col_ratio_list = list(np.array(self.initial_collateral_value_list) / self.initial_collateral_value_list[0])
        ncs_col_ratio_list = list(np.array(self.necessary_collateral_value_list) / self.necessary_collateral_value_list[0])
        price_ratio_lists = {}
        collateral_key_list = self.collateral_portfolio_list[0].keys()
        for key in collateral_key_list:
            init_price = self.collateral_portfolio_list[0][key]['price']
            price_ratio_lists[key] = [_p[key]['price'] / init_price for _p in self.collateral_portfolio_list]

        ax1.plot(self.date_list, init_col_ratio_list, marker='o', markersize=5, linewidth=3, color='red', label='担保資産価値平均')
        ax1.set_ylabel('初期価格に対する比率', fontsize=28, fontname="Hiragino Sans")
        ax1.plot(self.date_list, ncs_col_ratio_list, marker='o', markersize=5, linewidth=3, color='blue', label='現金（日本円）')

        for key, ratio_list in price_ratio_lists.items():
            ax1.plot(self.date_list, ratio_list, marker='o', markersize=2, linewidth=1, label=key[:-2])

        ax1.legend(loc=4, prop={"size": 24, "family": "Hiragino Sans"})
        ax1.tick_params(labelsize=24)
        ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax1.set_ylim(ymin=ymin)
        ax1.xaxis.offsetText.set_fontsize(24)
        ax1.yaxis.offsetText.set_fontsize(24)

    def plt_initial_collateral_portfolio_value(self) -> None:
        fig = plt.figure(figsize=(30, 15))
        ax = fig.add_subplot(1, 1, 1)
        plt.title('初期差入担保の総価値推移', fontsize=30, pad=20, fontname='Hiragino Sans')
        plt.plot(self.date_list, self.initial_collateral_value_list, marker='o', markersize=5, color='red')
        plt.xticks(fontsize=24)
        plt.yticks(fontsize=24)
        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax.yaxis.offsetText.set_fontsize(24)
        ax.xaxis.offsetText.set_fontsize(24)

    def plt_collateral_price_diff(self) -> None:
        # st, collateralの比較
        _fig, ax1 = plt.subplots(figsize=(30, 15))
        ax1_2 = ax1.twinx()

        # plt.title('実際の差入担保と必要担保価値の差分推移', fontsize=30, pad=20, fontname="Hiragino Sans")
        ax1.plot(self.date_list, self.collateral_sum_list, marker='o', markersize=5, color='red', label='Actual Collateral Value')
        ax1.set_ylabel('Actual Collateral Value', fontsize=20, fontname="Hiragino Sans")
        ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax1_2.plot(self.date_list, self.necessary_collateral_value_list, marker='o', markersize=5, color='blue', label='Necessary Collateral Value')
        ax1_2.set_ylabel('Necessary Collateral Value', fontsize=20, fontname="Hiragino Sans")
        ax1_2.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax1_2.set_ylim(ax1.get_ylim())
        handler1, label1 = ax1.get_legend_handles_labels()
        handler2, label2 = ax1_2.get_legend_handles_labels()

        ax1.legend(handler1 + handler2, label1 + label2, loc=2, borderaxespad=0., fontsize=20)
        ax1.tick_params(axis='y', colors='red', labelsize=15)
        ax1.yaxis.offsetText.set_fontsize(15)
        ax1.xaxis.offsetText.set_fontsize(15)
        ax1_2.xaxis.offsetText.set_fontsize(15)
        ax1_2.tick_params(axis='y', colors='blue', labelsize=15)
        ax1_2.yaxis.offsetText.set_fontsize(15)

    def bar_collateral_price_diff(self, ymax: Optional[float] = None, title: str = '', is_decimal: bool = False) -> int:
        fig = plt.figure(figsize=(45, 15))
        ax = fig.add_subplot(1, 1, 1)
        plt.title(title, fontsize=40, pad=20, fontname='Hiragino Sans')
        _price_diff_list = np.array(self.collateral_price_diff_list) / 1e+4
        plt.bar(self.date_list, _price_diff_list)
        plt.ylabel("実質差入担保価値と必要担保価値の価格差（万円）", fontsize=32, fontname="Hiragino Sans")
        # plt.xlabel("差入担保と必要担保金額の差額推移", fontname="Hiragino Sans")
        plt.xticks(fontsize=24)
        plt.yticks(fontsize=24)
        if ymax:
            plt.ylim(ymax=ymax)
        if not is_decimal:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
        # ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax.yaxis.offsetText.set_fontsize(24)
        ax.xaxis.offsetText.set_fontsize(24)

        plt.savefig(f'./data0118/{title[:4]}_price_diff_bar')

    def plt_collateral_percentage(self, ymin: int = -10, ymax: int = 10) -> None:
        # 差し入れている担保の割合の推移
        color_list = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
        security_list = self.collateral_portfolio_list[-1].keys()
        collateral_percentages = {}
        for security in security_list:
            collateral_percentages[security] = []
            for portfolio in self.collateral_portfolio_list:
                if security in portfolio:
                    collateral_percentages[security].append(portfolio[security]['num'] / self.initial_collateral_portfolio_list[0][security]['num'])
                else:
                    collateral_percentages[security].append(0)

        plt.figure(figsize=(30, 15))
        plt.title("差入担保の割合推移", fontsize=30, pad=20, fontname="Hiragino Sans")
        for idx, security in enumerate(security_list):
            plt.plot(self.date_list, collateral_percentages[security], marker='o', markersize=5, color=color_list[idx], label=security)
        plt.legend(loc=2, fontsize=28)

        date_lender_additional_issue = []
        for i, x in enumerate(self.lender_additional_issue_list):
            if x:
                date_lender_additional_issue.append(self.date_list[i])
        plt.vlines(date_lender_additional_issue, ymin=ymin, ymax=ymax, color='orange', linestyle='solid', linewidth=1)

        # date_borrower_additional_issue = []
        # for i, x in enumerate(self.borrower_additional_issue_list):
        #     if x:
        #         date_borrower_additional_issue.append(self.date_list[i])
        # plt.vlines(date_borrower_additional_issue, ymin=0.5, ymax=4, color='cyan', linestyle='solid', linewidth=1)
        return collateral_percentages

    def plt_collateral_num(self, ymin: int = -10, ymax: int = 10, show_additional_issue: bool = True, title: str = '') -> None:
        # 差し入れている担保の数量の推移
        color_list = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
        security_list = self.collateral_portfolio_list[-1].keys()
        collateral_percentages = {}
        for security in security_list:
            collateral_percentages[security] = []
            for portfolio in self.collateral_portfolio_list:
                if security in portfolio:
                    collateral_percentages[security].append(portfolio[security]['num'])
                else:
                    collateral_percentages[security].append(0)

        fig = plt.figure(figsize=(45, 15))
        ax = fig.add_subplot(1, 1, 1)
        plt.title(title, fontsize=40, pad=20, fontname='Hiragino Sans')
        for idx, security in enumerate(security_list):
            plt.plot(self.date_list, collateral_percentages[security], marker='o', markersize=5, color=color_list[idx], label=security)
        plt.legend(loc=2, fontsize=24)

        plt.xticks(fontsize=24)
        plt.yticks(fontsize=24)
        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax.yaxis.offsetText.set_fontsize(24)
        ax.xaxis.offsetText.set_fontsize(24)
        plt.ylabel('差入担保トークン数', fontsize=32, fontname='Hiragino Sans')

        if show_additional_issue:
            date_lender_additional_issue = []
            for i, x in enumerate(self.lender_additional_issue_list):
                if x:
                    date_lender_additional_issue.append(self.date_list[i])
            plt.vlines(date_lender_additional_issue, ymin=ymin, ymax=ymax, color='orange', linestyle='solid', linewidth=1)

            # date_borrower_additional_issue = []
            # for i, x in enumerate(self.borrower_additional_issue_list):
            #     if x:
            #         date_borrower_additional_issue.append(self.date_list[i])
            # plt.vlines(date_borrower_additional_issue, ymin=0.5, ymax=4, color='cyan', linestyle='solid', linewidth=1)

        plt.savefig(f'./data0118/{title[:4]}_collateral_num_plt')
        return collateral_percentages

    def stack_collateral_percentage(self, ymin: int = -10, ymax: int = 10, show_additional_issue: bool = True, title: str = '') -> None:
        # 差し入れている担保の数量の推移
        color_list = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink'][:5]  # 必要に応じて追加（もしくはautoにする）
        security_list = [item[0] for item in sorted(self.collateral_portfolio_list[-1].items(), key=lambda x: x[1]['priority'], reverse=True)]
        collateral_percentages = {}
        for security in security_list:
            collateral_percentages[security] = []
            for portfolio in self.collateral_portfolio_list:
                if security in portfolio:
                    collateral_percentages[security].append(portfolio[security]['num'] / self.initial_collateral_portfolio_list[0][security]['num'])
                else:
                    collateral_percentages[security].append(0)

        fig = plt.figure(figsize=(45, 15))
        ax = fig.add_subplot(1, 1, 1)
        plt.title(title, fontsize=48, pad=20, fontname='Hiragino Sans')

        plt.stackplot(self.date_list, list(reversed(collateral_percentages.values())), colors=reversed(color_list), labels=reversed([label[:-2] for label in security_list]))

        # offsets = np.zeros(len(self.date_list))
        # # plt.bar(self.date_list, collateral_percentages[security_list[-1]], bottom=offsets, color=color_list[-1], label=security_list[-1], align='center')
        # for i in range(len(security_list) - 1, -1, -1):
        #     # idx = len(security_list) - i - 1
        #     plt.bar(self.date_list, collateral_percentages[security_list[i]], bottom=offsets, color=color_list[i], label=security_list[i], align='center')
        #     offsets += np.array(collateral_percentages[security_list[i]])
        #     print(offsets)
        #     # plt.plot(self.date_list, collateral_percentages[security], marker='o', markersize=5, color=color_list[idx], label=security)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc=2, fontsize=24)

        plt.xticks(fontsize=24)
        plt.yticks(fontsize=24)
        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax.yaxis.offsetText.set_fontsize(24)
        ax.xaxis.offsetText.set_fontsize(24)
        plt.ylabel('差入担保トークン数（初期差入量に対する比率）', fontsize=40, fontname='Hiragino Sans')

        if show_additional_issue:
            date_lender_additional_issue = []
            for i, x in enumerate(self.lender_additional_issue_list):
                if x:
                    date_lender_additional_issue.append(self.date_list[i])
            plt.vlines(date_lender_additional_issue, ymin=ymin, ymax=ymax, color='orange', linestyle='solid', linewidth=1)

            # date_borrower_additional_issue = []
            # for i, x in enumerate(self.borrower_additional_issue_list):
            #     if x:
            #         date_borrower_additional_issue.append(self.date_list[i])
            # plt.vlines(date_borrower_additional_issue, ymin=0.5, ymax=4, color='cyan', linestyle='solid', linewidth=1)

        plt.savefig(f'./data0118/{title[:4]}_collateral_num_stk')
        return collateral_percentages

    def bar_collateral_percentage(self, ymin: int = -10, ymax: int = 10, show_additional_issue: bool = True, title: str = '') -> None:
        # 差し入れている担保の数量の推移
        color_list = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink'][:5]  # 必要に応じて追加（もしくはautoにする）
        security_list = [item[0] for item in sorted(self.collateral_portfolio_list[-1].items(), key=lambda x: x[1]['priority'], reverse=True)]
        collateral_percentages = {}
        for security in security_list:
            collateral_percentages[security] = []
            for portfolio in self.collateral_portfolio_list:
                if security in portfolio:
                    collateral_percentages[security].append(portfolio[security]['num'] / self.initial_collateral_portfolio_list[0][security]['num'])
                else:
                    collateral_percentages[security].append(0)

        fig = plt.figure(figsize=(45, 15))
        ax = fig.add_subplot(1, 1, 1)
        plt.title(title, fontsize=48, pad=20, fontname='Hiragino Sans')

        offsets = np.zeros(len(self.date_list))
        # plt.bar(self.date_list, collateral_percentages[security_list[-1]], bottom=offsets, color=color_list[-1], label=security_list[-1], align='center')
        for i in range(len(security_list) - 1, -1, -1):
            # idx = len(security_list) - i - 1
            plt.bar(self.date_list, collateral_percentages[security_list[i]], bottom=offsets, color=color_list[i], label=security_list[i][:-2], align='center')
            offsets += np.array(collateral_percentages[security_list[i]])
            # print(offsets)
            # plt.plot(self.date_list, collateral_percentages[security], marker='o', markersize=5, color=color_list[idx], label=security)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc=2, fontsize=24)

        plt.xticks(fontsize=24)
        plt.yticks(fontsize=24)
        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax.yaxis.offsetText.set_fontsize(24)
        ax.xaxis.offsetText.set_fontsize(24)
        plt.ylabel('差入担保トークン数（初期差入量に対する比率）', fontsize=40, fontname='Hiragino Sans')

        if show_additional_issue:
            date_lender_additional_issue = []
            for i, x in enumerate(self.lender_additional_issue_list):
                if x:
                    date_lender_additional_issue.append(self.date_list[i])
            plt.vlines(date_lender_additional_issue, ymin=ymin, ymax=ymax, color='orange', linestyle='solid', linewidth=1)

            # date_borrower_additional_issue = []
            # for i, x in enumerate(self.borrower_additional_issue_list):
            #     if x:
            #         date_borrower_additional_issue.append(self.date_list[i])
            # plt.vlines(date_borrower_additional_issue, ymin=0.5, ymax=4, color='cyan', linestyle='solid', linewidth=1)

        plt.savefig(f'./data0118/{title[:4]}_collateral_num_bar')
        return collateral_percentages

    def bar_collateral_num(self, ymin: int = -10, ymax: int = 10, show_additional_issue: bool = True, title: str = '') -> None:
        # 差し入れている担保の数量の推移
        color_list = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink'][:5]  # 必要に応じて追加（もしくはautoにする）
        security_list = [item[0] for item in sorted(self.collateral_portfolio_list[-1].items(), key=lambda x: x[1]['priority'], reverse=True)]
        collateral_percentages = {}
        negative_num_list = []
        for idx, security in enumerate(security_list):
            collateral_percentages[security] = []
            for portfolio in self.collateral_portfolio_list:
                if security in portfolio:
                    collateral_num = portfolio[security]['num']
                    if collateral_num >= 0:
                        collateral_percentages[security].append(collateral_num)
                        if idx == 0:
                            negative_num_list.append(0)
                    else:
                        collateral_percentages[security].append(0)
                        negative_num_list.append(collateral_num)
                else:
                    collateral_percentages[security].append(0)

        fig = plt.figure(figsize=(45, 15))
        ax = fig.add_subplot(1, 1, 1)
        plt.title(title, fontsize=48, pad=20, fontname='Hiragino Sans')

        offsets = np.zeros(len(self.date_list))
        for i in range(len(security_list) - 1, -1, -1):
            plt.bar(self.date_list, collateral_percentages[security_list[i]], bottom=offsets, color=color_list[i], label=security_list[i][:-2], align='center')
            offsets += np.array(collateral_percentages[security_list[i]])

        # 単一トークン価値調整時に負の値を持つ（余剰返還分）場合をプロット
        if any(negative_num_list):
            plt.bar(self.date_list, negative_num_list, color=color_list[0], label=security_list[0][:-2], align='center')

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc=2, fontsize=24)

        plt.xticks(fontsize=24)
        plt.yticks(fontsize=24)
        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        ax.yaxis.offsetText.set_fontsize(24)
        ax.xaxis.offsetText.set_fontsize(24)
        plt.ylabel('差入担保トークン数', fontsize=40, fontname='Hiragino Sans')

        if show_additional_issue:
            date_lender_additional_issue = []
            for i, x in enumerate(self.lender_additional_issue_list):
                if x:
                    date_lender_additional_issue.append(self.date_list[i])
            plt.vlines(date_lender_additional_issue, ymin=ymin, ymax=ymax, color='orange', linestyle='solid', linewidth=3)

            # date_borrower_additional_issue = []
            # for i, x in enumerate(self.borrower_additional_issue_list):
            #     if x:
            #         date_borrower_additional_issue.append(self.date_list[i])
            # plt.vlines(date_borrower_additional_issue, ymin=0.5, ymax=4, color='cyan', linestyle='solid', linewidth=1)

        plt.savefig(f'./data0118/{title[:4]}_collateral_num_bar')
        return collateral_percentages
