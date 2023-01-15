# mozchart: Mozaic Chart Creator
# This module is to create a 2D percentile mozaic chart with 3 functions
#
# 1) [ctab] to extract adjusted cross-tab dataframe and series for xlabel
# 2) [mplot] to plot mozaic chart
# 3) [chart] to create mozaic chart directly from given dataframe
#
# Import module
import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt

def ctab (d_frame, y_col, x_col, filter_col = None, filter_val = None):
    '''
    Function to extract adjusted cross-tab dataframe and series for xlabel
    to be used in making mozaic chart from given dataframe 
    INPUT
    d_frame: dataframe to be processed
    y_col: str, column to be value and ylabel
    x_col: str, column to be xlabel
    filter_col: str, column to apply filer
    filter_val: value of filter
    OUTPUT
    d_frame_adj: cross-tab dataframe adjusted to make chart
    sr_column_portion_adj: series to make xlabel of chart
    '''
    if filter_col == None:
        df = d_frame
    else:
        df = d_frame[d_frame[filter_col] == filter_val]
    
    # for missing value to be filled with 'UNID' for dist plot
    df.fillna({y_col : 'UNID', x_col : 'UNID'}, inplace = True)
    
    data = pd.crosstab(df[y_col], df[x_col], normalize = 'columns', 
                       margins = True).sort_values(by = 'All', ascending = False)
    data.insert(0, 'Total', data['All'])
    data.insert(1, '', np.nan)
    d_frame_adj = data.drop('All', axis = 1)
        
    sr = pd.crosstab(df[y_col], df[x_col], normalize = 'index', margins = True)
    sr = sr.loc['All']
    sr_column_portion_adj = pd.concat([pd.Series([np.nan, np.nan], ['Total', np.nan]), sr])
    
    if filter_col == None:
        chart_title = y_col + ' by ' + x_col
    else:
        chart_title = y_col + ' by ' + x_col + ' (' + filter_col + ': ' + filter_val + ')' 
    
    return d_frame_adj, sr_column_portion_adj, chart_title

def mplot (d_frame_adj, sr_column_portion_adj, fig_size = (10, 5), min_dis_val = 3,
           chart_title = '', fixed_color = []):
    '''
    Function to plot mozaic chart using d_frame_adj made by moz_ctab or moz_ctab_adj
    INPUT
    d_frame_adj: cross-tab dataframe made by moz_ctab or moz_ctab_adj
    sr_column_portion_adj: series of xlabel made by moz_ctab or moz_ctab_adj
    fig_size: tuple, figsize, defalut as (12, 5)
    min_dis_val: float, threshold in value display of chart, default as 3
    chart_title: str, text of chart
    fixed_color: list, list of colors pre-made for ylabel
    OUTPUT
    mozaic chart
    '''      
    # base data for chart body, ytick and table
    base_num = d_frame_adj * 100   
    
    ### dataframe of chart body: reversed data of base_num
    df_chart = base_num.reindex(index = base_num.index[::-1])
    
    ##### bottom points to stacked parts
    df_chart_cumsum = df_chart.cumsum().set_index(df_chart.index.astype(str) + '_cs')
    df_chart_cumsum_shift = df_chart_cumsum.shift(periods = 1, fill_value = 0)
    bottom_list = []
    for i in df_chart_cumsum_shift.index:
        globals()[i] = list(df_chart_cumsum_shift.loc[i])
        bottom_list.append(globals()[i])
    
    ##### heights and values of stacked parts
    value_list = []
    for i in df_chart.index:
        globals()[i] = list(df_chart.loc[i])
        value_list.append(globals()[i])
    
    ##### points of ytick  
    df_ytick = (df_chart_cumsum + df_chart_cumsum_shift) / 2
    ytick_list = []
    for i in df_ytick.index:
        globals()[i] = list(df_ytick.loc[i])
        ytick_list.append(globals()[i])

    ##### ylabels
    df_ylabel = df_chart.copy()
    df_ylabel['ylabels'] = np.where(df_ylabel['Total'] > min_dis_val, df_ylabel.index, '')
    ylabels = list(df_ylabel['ylabels'])
   
    ### dataframe of table
    df_table = base_num.drop('', axis = 1).fillna(0).round(decimals = 0).astype('int')
    df_table.replace(0, '', inplace = True)
    df_table = df_table.iloc[:20]

    # base data for xtick
    sr_column_portion_adj = sr_column_portion_adj.fillna(0)
    xtick_num = list(sr_column_portion_adj * 100)
    xtick_data = xtick_num[2:]
    xtick_data_sum = sum(xtick_data)
    
    ##### widths of bars
    xtick_width = [100 * i / xtick_data_sum for i in xtick_data]
    width = [15, 5] + xtick_width
       
    ##### start points of bars
    xPoint_num, xPoint = 0, [0]
    for i in width[:-1]:
        xPoint_num += i
        xPoint.append(xPoint_num)

    ##### points of xtick
    xPoint_120 = xPoint.copy()
    xPoint_120.append(120)
    xtick_Point = []
    for i, j in zip(xPoint_120[:-1], xPoint_120[1:]):
        xtick_Point.append((i + j)/2)

    ##### xlabels
    xtick_add = [int(round(i, 0)) for i in xtick_data]
    xtick_add = ['', ''] + xtick_add  
    xlabels = [f"{x1}\n{x2}" for x1, x2, in zip(df_chart.columns, xtick_add)]
    
    # color list
    def mozaic_chart_color (d_frame_adj, fixed_color):
        if d_frame_adj.shape[0] == len(fixed_color):
            color_list = fixed_color
        else:
            color_list = []
            for i in d_frame_adj.index:
                color_list.append(["#"+''.join([random.choice('ABCDEF89') for i in range(6)])])
        return color_list
    color_list = mozaic_chart_color(d_frame_adj, fixed_color)

    # chart plot
    fig, ax = plt.subplots(figsize = fig_size)

    for i, j in enumerate(value_list):      
        bar = ax.bar(xPoint, width = width, height = j, bottom = bottom_list[i],
                     align = 'edge', color = color_list[i], edgecolor = 'gray')
        for k, l in enumerate(j):
            plt.text(xtick_Point[k], ytick_list[i][k], 
                     '%.0f' %l if l > min_dis_val else '',
                     ha = 'center', va = 'center', size = fig_size[1] * 2)
    plt.rcParams['font.family'] = 'Arial'
    
    plt.xticks(xtick_Point, xlabels, size = fig_size[1] * 2.1, family ='Arial');
    plt.tick_params(axis= 'x', length = 0, pad = fig_size[1])
    plt.yticks(df_ytick['Total'], ylabels, size = fig_size[1] * 2.1, family ='Arial');
    ax.margins(x = 0.02);
    plt.tick_params(axis = 'y', length = 0)

    plt.axhline(color='gray', linestyle='solid', linewidth=2);
    plt.box(False)
    
    # table = ax.table(
    #     cellText=df_table.values, rowLabels = df_table.index, rowLoc = 'right',
    #     colLabels=df_table.columns, cellLoc = 'center',
    #     bbox=[0.015,-0.92,0.97,0.8]);
    # table.set_fontsize(fig_size[1] * 1.8)

    plt.title(chart_title, size = fig_size[1] * 2.2);
    fig.suptitle('(%)', size = fig_size[1] * 2, x=0.88, y=0.88, ha = 'right');

def chart (d_frame, y_col, x_col, filter_col = None, filter_val = None,
           fig_size = (10, 5), min_dis_val = 3, chart_title = '', fixed_color = []):
    '''
    Function composed of nested functions of module to plot mozic chart from given dataframe
    INPUT
    d_frame: dataframe to be processed
    y_col: str, column to be value and ylabel
    x_col: str, column to be xlabel
    filter_col: str, column to apply filer
    filter_val: value of filter
    fig_size: tuple, figsize, defalut as (12, 5)
    min_dis_val: float, threshold in value display of chart, default as 3
    chart_title: str, text of chart
    fixed_color: list, list of colors pre-made for ylabel
    OUTPUT
    mozaic chart
    '''        
    d_frame_adj, sr_column_portion_adj, chart_title = ctab (d_frame, y_col, x_col,
                                                            filter_col, filter_val)
    mplot (d_frame_adj, sr_column_portion_adj, fig_size, min_dis_val, chart_title, fixed_color)