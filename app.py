from datetime import date, timedelta
import dash
from dash import dcc
from dash import html
from dash import dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import pandas as pd
import numpy as np
import math
import requests
import json
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from config import (
    KEY,
    TOKEN,
    BACKLOG_ID,
    CURRENT_TASKS_ID,
    TASKS_FOR_LATER_ID,
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_NAME,
    DATABASE_PORT
)

from library import get_count_cards_in_column

""" READ DATA """

con = psycopg2.connect(
    database=DATABASE_NAME,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    host=DATABASE_HOST,
    port=DATABASE_PORT
)

def create_link(row):
    if row['link'] is not None:
        row['cardname'] = "<a href='" + "https://trello.com/c/" + row[
            'link'] + "' target='_blank'>" + row['cardname'] + "</a>"
    return row


def get_data(sql_query):
    """ query parts from the parts table """
    try:
        cur = con.cursor()
        cur.execute(sql_query)
        rows = cur.fetchall()
        cur.close()
        return rows
    except (Exception, psycopg2.DatabaseError) as error:
        print('походу ошибка', error)


sql_query_add_minus_remove_task = """select coalesce(movefromtrash, 0) as 
movefromtrash, 0 as movetotrash, coalesce(addCard, 0) as addcard, coalesce(
deleteintrash, 0) as deleteintrash, T.date as date, 'backlog' as "columns" 
from ( select generate_series('2021-09-01', current_date, 
'1 day'::interval)::date as date ) T left join ( select count(id) as 
addCard, date(date) as date from trello.createcard where listname = 
'Корзина' group by date(date) order by date ) T0 on T0.date = T.date left 
join ( select count(id) movefromtrash, date(date) as date from 
trello.cardmove where listbeforename = 'Корзина' group by date(date) order 
by date ) T1 on T1.date = T.date left join ( select count(id) deleteintrash, 
date(date) as date from trello.deletecard d where listname = 'Корзина' group 
by date(date) order by date ) T2 on T2.date = T.date union all select 
coalesce(movefromtrash, 0) as movefromtrash, coalesce(movetotrash, 
0) as movetotrash, coalesce(addCard, 0) as addcard, coalesce(deleteintrash, 
0) as deleteintrash, T.date as date, 'сurrent tasks' as "columns" from ( 
select generate_series('2021-09-01', current_date, '1 day'::interval)::date 
as date ) T left join ( select count(id) as addCard, date(date) from 
trello.createcard where listid = '5fa291a201e844109fca5061' group by date(
date) order by date ) T0 on T0.date = T.date left join ( select count(id) 
movefromtrash, date(date) from trello.cardmove where listbeforeid = 
'5fa291a201e844109fca5061' group by date(date) order by date ) T1 on date(
T1.date) = date(T.date) left join ( select count(id) movetotrash, date(date) 
from trello.cardmove where listafterid = '5fa291a201e844109fca5061' group by 
date(date) order by date ) T2 on date(T2.date) = date(T.date) left join ( 
select count(id) deleteintrash, date(date) from trello.deletecard d where 
listid = '5fa291a201e844109fca5061' group by date(date) order by date ) T3 
on date(T3.date) = date(T.date) """

sql_query_trash = """

	select 
    	coalesce(movefromtrash, 0) as movefromtrash,
    	coalesce(addCard, 0) as addcard,
    	coalesce(deleteintrash, 0) as deleteintrash,
    	T.date as date
    from
    	(	
    	select generate_series('2021-09-01', current_date, '1 day'::interval)::date as date
    	) T
    	left join
    	(
    		select 
    			count(id) as addCard,
    			date(date) as date
    		from trello.createcard 
    		where listname = 'Корзина'
    		group by date(date)
    		order by date
    	) T0
    	on T0.date = T.date
    	left join
    		(	
    			select 
    				count(id) movefromtrash,
    				date(date) as date
    			from trello.cardmove
    			where listbeforename = 'Корзина'
    			group by date(date)
    			order by date
    		) T1
    		on T1.date = T.date
    	left join 
    		(
    			select 
    				count(id) deleteintrash,
    				date(date) as date
    			from trello.deletecard d 
    			where listname = 'Корзина'
    			group by date(date)
    			order by date
    		) T2
    		on T2.date = T.date
"""

sql_query_action = """
    select 
    	coalesce(movefromtrash, 0) as movefromtrash,
    	coalesce(movetotrash, 0) as movetotrash,
    	coalesce(addCard, 0) as addcard,
    	coalesce(deleteintrash, 0) as deleteintrash,
    	T.date as date
from 
    (
    	select generate_series('2021-09-01', current_date, '1 day'::interval)::date as date
    ) T
    left join
    	(
    		select 
    			count(id) as addCard,
    			date(date)
    		from trello.createcard 
    		where listid = '5fa291a201e844109fca5061'
    		group by date(date)
    		order by date
    	) T0
    	on T0.date = T.date
    left join
    	(	
    		select 
    			count(id) movefromtrash,
    			date(date)
    		from trello.cardmove
    		where listbeforeid = '5fa291a201e844109fca5061'
    		group by date(date)
    		order by date
    	) T1
    		on date(T1.date) = date(T.date)
    left join
    	(	
    		select 
    			count(id) movetotrash,
    			date(date)
    		from trello.cardmove
    		where listafterid = '5fa291a201e844109fca5061'
    		group by date(date)
    		order by date
    	) T2
    	on date(T2.date) = date(T.date)
    	left join 
    		(
    			select 
    				count(id) deleteintrash,
    				date(date)
    			from trello.deletecard d 
    			where listid = '5fa291a201e844109fca5061'
    			group by date(date)
    			order by date
    		) T3
    		on date(T3.date) = date(T.date)"""

sql_query_rating = """
select card_rating.cardid,
       card_rating.cardname,
       card_rating.listid,
       card_rating.listname,
       card_rating.date,
       card_link.link
  from (
        select cardid,
               cardname,
               listid,
               listname, date
          from trello.createcard
         where createcard.listid = '5fa291a201e844109fca505f'
           and id <> cardid
           and cardid not in (
                select cardid
                  from trello.deletecard d
                 where listid = '5fa291a201e844109fca505f'
                 union select cardid
                  from trello.cardmove c
                 where listbeforeid = '5fa291a201e844109fca505f'
               )
         union select cardid,
               cardname,
               listid,
               listname, date
          from (
                select cardid,
                       cardname,
                       listid,
                       listname, date
                  from trello.createcard c
                 where listid = '5fa291a201e844109fca5061'
                 union select cardid,
                       cardname,
                       listafterid as listid,
                       listaftername as listname, date
                  from trello.cardmove
                 where listafterid = '5fa291a201e844109fca5061'
               ) nowdo
         where nowdo.date > '2021-11-01'
           and nowdo.cardid not in (
                select cardid
                  from trello.deletecard d
                 where listid = '5fa291a201e844109fca5061'
                 union select cardid
                  from trello.cardmove c
                 where listbeforeid = '5fa291a201e844109fca5061'
               )
       ) card_rating
  left join trello.card_link
    on card_link.id_card = card_rating.cardid
"""

# average card insert into корзина list every day
avg_add_trash_evday = '''select count(*) / (extract(day from current_date - (select min(date) from trello.createcard where listid = '5fa291a201e844109fca505f')))
from trello.createcard c 
where listid = '5fa291a201e844109fca505f'
'''
# average card insert into текущие действия list every day
avg_add_action_evday = '''
select (c2.countcardadd + c1.countcardmove) / (extract(day from current_date - (select min(date) from trello.cardmove where listafterid = '5fa291a201e844109fca5061')))
from 
	(
		select count(*) as countcardmove
		from trello.cardmove c 
		where listafterid = '5fa291a201e844109fca5061'
	) c1,
	(
		select count(*) as countcardadd
		from trello.createcard c 
		where listid = '5fa291a201e844109fca5061'
	) c2
'''

sql_finished_trash = '''
select count(*)
from
	(
		select 
			id,
			cardid,
			listid,
			type,
			date
		from trello.deletecard d 
		where date(date) = current_date
			and listid = '5fa291a201e844109fca505f'
		union 
		select
			id,
			cardid,
			listbeforeid,
			type,
			date
		from trello.cardmove c 
		where date(date) = current_date
			and listbeforeid = '5fa291a201e844109fca505f'
	) finished
'''

sql_finished_action = '''
select count(*)
from
	(
		select 
			id,
			cardid,
			listid,
			type,
			date
		from trello.deletecard d 
		where date(date) = current_date
			and listid = '5fa291a201e844109fca5061'
		union 
		select
			id,
			cardid,
			listbeforeid,
			type,
			date
		from trello.cardmove c 
		where date(date) = current_date
			and listbeforeid = '5fa291a201e844109fca5061'
	) finished
'''

avgTimeCardTrash = '''
select avg(extract(epoch from (endDate::timestamp - startDate::timestamp)))
from
(
	select 
		c."date" as startDate,
		d."date" as endDate
	from trello.createcard c 
		inner join trello.deletecard d 
			on d.cardid = c.cardid 
				and d.listid = '5fa291a201e844109fca505f'
	where c.listid = '5fa291a201e844109fca505f'
	union
	select 
		c."date" as startDate,
		c2."date" as endDate
	from trello.createcard c 
		inner join trello.cardmove c2 
			on c2.cardid = c.cardid
				and c2.listbeforeid = '5fa291a201e844109fca505f'
	where c.listid = '5fa291a201e844109fca505f'
) avgTimeCardTrash
'''

avgTimeCardAction = '''
select avg(extract(epoch from (endDate::timestamp - startDate::timestamp)))
from
(
	select 
		c."date" as startDate,
		d."date" as endDate
	from 
		(
			select 
				c.cardid,
				c."date" 
			from trello.createcard c 
			where listid = '5fa291a201e844109fca5061'
			union 
			select 
				c2.cardid,
				c2."date" 
			from trello.cardmove c2 
			where listafterid = '5fa291a201e844109fca5061'
		)c 
		inner join trello.deletecard d 
			on d.cardid = c.cardid 
				and d.listid = '5fa291a201e844109fca5061'
	union
	select 
		c."date" as startDate,
		c2."date" as endDate
	from 
		(
			select 
				c.cardid,
				c."date" 
			from trello.createcard c 
			where listid = '5fa291a201e844109fca5061'
			union 
			select 
				c2.cardid,
				c2."date" 
			from trello.cardmove c2 
			where listafterid = '5fa291a201e844109fca5061'
		) c 
		inner join trello.cardmove c2 
			on c2.cardid = c.cardid
				and c2.listbeforeid = '5fa291a201e844109fca5061'
) avgTimeCardAction
'''

sql_query_quantity_change = """
select case when list_id = '5fa291a201e844109fca505f' then 'backlog'
            when list_id = '5fa291a201e844109fca5061' then 'current tasks'
            when list_id = '5fa2f9f37004cf1fda6f96b8' then 'tasks till later'
             end as list_id,
       date(date_time),
       max(quantity)
  from trello.quantity_change
 group by date(date_time),
          list_id
 order by date(date_time)
"""

CHART_TEMPLATE = go.layout.Template(
    layout=dict(
        font=dict(family='Century Gothic',
                  size=14),
        legend=dict(orientation='h',
                    x=0,
                    y=1.1)
    ),
)

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5,'}]
                )

card_icon = {
    "color": "white",
    "textAlign": "center",
    "fontSize": 30,
    "margin": "auto",
}

app.layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.Div([
                dbc.Button("Settings", id="open-offcanvas", n_clicks=0,
                           style={"margin-top": "10px", "position": "relative",
                                  "float": "right"}),
                dbc.Offcanvas(
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                dcc.DatePickerRange(
                                    id='my-date-picker-range',
                                    display_format='DD.MM.YY',
                                    initial_visible_month=date.today(),
                                    start_date=date.today() - timedelta(
                                        days=7),
                                    end_date=date.today()
                                ),
                                html.Div(
                                    id='output-container-date-picker-range')
                            ], md=10, style={"margin": "0 auto"}),
                        ], justify="end")
                        # ,
                        # dbc.Row([
                        #     dbc.Col([
                        #         html.Div([
                        #             dcc.RadioItems(
                        #                 id='regim_work',
                        #                 options=[dict(label='Auto', value='auto'),
                        #                          dict(label='Manual', value='manual')],
                        #                 value='A')
                        #         ])
                        #     ], md=3)
                        # ])
                    ]),
                    id="offcanvas",
                    title="Title",
                    is_open=False,
                ),
            ])
        ], md=2)
    ], justify="end"),
    dbc.Row([
        dbc.Col([
            dbc.CardGroup([
                dbc.Card(
                    dbc.CardBody([
                        html.H5(id='action_count',
                                className="card-title"),
                        html.P("Backlog", className="card-text"),
                    ])
                ),
                dbc.Card(
                    html.Div(className="fa fa-trash", style=card_icon),
                    className="bg-primary",
                    style={"maxWidth": 75},
                ),
            ], className="mt-4 shadow")
        ], md=4),
        dbc.Col([
            dbc.CardGroup([
                dbc.Card(
                    dbc.CardBody([
                        html.H5(id='current_tasks_count',
                                className="card-title"),
                        html.P("Current task",
                               className="card-text", )
                    ])
                ),
                dbc.Card(
                    html.Div(className="fa fa-check-square",
                             style=card_icon),
                    className="bg-primary",
                    style={"maxWidth": 75},
                ),
            ], className="mt-4 shadow")
        ]),
        dbc.Col([
            dbc.CardGroup([
                dbc.Card(
                    dbc.CardBody([
                        html.H5(id='tasks_for_later_count',
                                className="card-title"),
                        html.P("Tasks till later",
                               className="card-text", ),
                    ])
                ),
                dbc.Card(
                    html.Div(className="fa fa-book", style=card_icon),
                    className="bg-primary",
                    style={"maxWidth": 75},
                ),
            ], className="mt-4 shadow")
        ], md=4)
    ]),
    dbc.Row([
        dbc.Col([
            html.Div('Difference between incoming and outcoming cards',
                     style={"text-align": "center"}),
            dcc.Graph(id='action',
                      config={'displayModeBar': False}
                      ),
            dcc.Interval(
                id='interval-component',
                interval=10 * 1000,  # in milliseconds
                n_intervals=0)
        ], md=6),
        dbc.Col([
            html.Div('Number of cards in columns',
                     style={"text-align": "center"}),
            dcc.Graph(id='quantity_change',
                      config={
                          'displayModeBar': False}
                      )
        ], md=6)
    ], style={"margin-top": "10px"}),
    dbc.Row(
        html.Div(id='data-table'),
        style={'margin-left': '30px',
               'margin-right': '30px',
               "margin-bottom": "30px"}
    )
], style={"width": "95%",
          "margin": "0 auto"})


@app.callback(
    [Output(component_id='action', component_property='figure'),
     Output(component_id='data-table', component_property='children'),
     Output(component_id='action_count', component_property='children'),
     Output(component_id='current_tasks_count', component_property='children'),
     Output(component_id='tasks_for_later_count',
            component_property='children'),
     Output(component_id='quantity_change', component_property='figure')],
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('interval-component', 'n_intervals')]
)
def update_graph_live(start_date, end_date, n):
    sql_action = get_data(sql_query_add_minus_remove_task)
    df = pd.DataFrame(sql_action,
                      columns=['movefromtrash', 'movetotrash', 'addcard',
                               'deleteintrash', 'date', 'columns'])
    df['result'] = df['movefromtrash'] + df['deleteintrash'] - df[
        'movetotrash'] - df['addcard']
    chart_data2 = df[(pd.to_datetime(df['date']) >= start_date) &
                     (pd.to_datetime(df['date']) <= end_date)]
    fig2 = px.bar(chart_data2, x='date', y='result', color='columns',
                  barmode="group")
    fig2.update_layout(template=CHART_TEMPLATE, legend_title_text='')

    rating = get_data(sql_query_rating)
    rating = pd.DataFrame(rating,
                          columns=['cardid', 'cardname', 'listid', 'listname',
                                   'date', 'link'])
    rating['rank'] = np.where(rating['listid'] == '5fa291a201e844109fca505f',
                              round(len(rating[rating[
                                                   'listid'] == '5fa291a201e844109fca505f']) /
                                    get_data(avg_add_trash_evday)[0][0] + (
                                            pd.Timestamp.now() - pd.to_datetime(
                                        rating['date'].dt.tz_localize(
                                            None))).dt.total_seconds() /
                                    get_data(avgTimeCardTrash)[0][0], 2), None)
    rating.loc[:, 'rank'] = np.where(
        rating['listid'] == '5fa291a201e844109fca5061', round(
            len(rating[rating['listid'] == '5fa291a201e844109fca5061']) /
            get_data(avg_add_action_evday)[0][0] + (
                    pd.Timestamp.now() - pd.to_datetime(
                rating['date'].dt.tz_localize(None))).dt.total_seconds() /
            get_data(avgTimeCardAction)[0][0], 2), rating['rank'])
    rating = rating.apply(create_link, axis='columns')

    rating = rating.sort_values(by=['rank'], ascending=False)
    rating = rating.drop(columns=['cardid', 'listid', 'link'])

    avg_add_card_evday = math.ceil(get_data(avg_add_trash_evday)[0][0] +
                                   get_data(avg_add_action_evday)[0][0])
    finished_card_td = get_data(sql_finished_trash)[0][0] + \
                       get_data(sql_finished_action)[0][0]

    quan_card_left = avg_add_card_evday - finished_card_td
    if quan_card_left >= 0:
        quan_card_left = quan_card_left
    else:
        quan_card_left = 0

    rating = rating.iloc[:quan_card_left]

    tbl = dash_table.DataTable(data=rating.to_dict('records'),
                               columns=[{'name': i, 'id': i,
                                         'presentation': 'markdown'}
                                        for i in rating.columns],
                               style_data={'width': '80px',
                                           'maxWidth': '80px',
                                           'minWidth': '80px'},
                               page_size=30,
                               style_header={'textAlign': 'center'},
                               markdown_options={"html": True})

    action_count = len(json.loads(get_count_cards_in_column(BACKLOG_ID).text))
    current_task_count = len(
        json.loads(get_count_cards_in_column(CURRENT_TASKS_ID).text))
    tasks_for_later_count = len(
        json.loads(get_count_cards_in_column(TASKS_FOR_LATER_ID).text))

    sql_quantity_change = get_data(sql_query_quantity_change)
    df3 = pd.DataFrame(sql_quantity_change,
                       columns=['list_id', 'date_time', 'quantity'])
    chart_data = df3[(pd.to_datetime(df3['date_time']) >= start_date) &
                     (pd.to_datetime(df3['date_time']) <= end_date)]

    fig = px.line(chart_data, x='date_time', y='quantity', color='list_id',
                  markers=True)
    fig.update_layout(template=CHART_TEMPLATE, legend_title_text='')

    return fig2, tbl, action_count, current_task_count, tasks_for_later_count, \
           fig


@app.callback(
    Output("offcanvas", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    [State("offcanvas", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(
        # host='192.168.1.68',
        debug=True)
