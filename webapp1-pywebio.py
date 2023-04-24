from functools import partial
import time
from pywebio.input import input, FLOAT
from pywebio.output import put_text, put_table, put_row, put_code, put_column, put_grid, span, put_markdown, put_html, \
    put_buttons, put_file, use_scope, put_tabs, put_widget
from pywebio import start_server
import mysql.connector
import os
import dotenv

dotenv.load_dotenv(".env")

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]
xtb_userId = os.environ["xtb_userId"]
xtb_passw = os.environ["xtb_pw"]


db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)

# ==================================================================================================================
# FUNKCIE


def add_buttons_to_db_output(db_out, symbol):
    final_list = []

    for row_tuple in db_out:
        row_list = list(row_tuple)

        buy_bool = row_list[1]
        sell_bool = row_list[2]
        timeframe = row_list[0]

        button1 = determine_button_type(buy_bool, symbol, timeframe)
        button2 = determine_button_type(sell_bool, symbol, timeframe)

        row_list[1] = button1
        row_list[2] = button2

        row_tuple = tuple(row_list)
        # row_tuple = row_tuple + (button1, button2)
        final_list.append(row_tuple)
    return final_list


def set_buy_to_false(params, placeholder):
    symbol = params[0]
    timeframe = params[1]

    # put_text(f"You clicked button {symbol} {timeframe}")
    q = f'update fri_trade.active_symbols set buyAllowed = False where symbol = "{symbol}" and timeframe = "{timeframe}"'
    fri_trade_cursor.execute(q)
    main()


def set_buy_to_true(params, placeholder):
    symbol = params[0]
    timeframe = params[1]

    q = f'update fri_trade.active_symbols set buyAllowed = True where symbol = "{symbol}" and timeframe = "{timeframe}"'
    fri_trade_cursor.execute(q)
    main()


def change_button(symbol, timeframe):
    determine_button_type(False, symbol, timeframe)


def determine_button_type(op_bool, symbol, timeframe):
    if op_bool:
        res = put_buttons([dict(label='TRUE', value='xxx', color='success')], onclick=partial(set_buy_to_false,
                                                                                              (symbol, timeframe)
                                                                                              ))
        return res
    else:
        res = put_buttons([dict(label='FALSE', value='xxx', color='danger')], onclick=partial(set_buy_to_true,
                                                                                              (symbol, timeframe)
                                                                                              ))
        return res















# ==================================================================================================================


def main():
    scope_name = "main_scope"

    q = f'SELECT symbol FROM fri_trade.active_symbols'
    fri_trade_cursor.execute(q)
    templist = fri_trade_cursor.fetchall()
    symbols = []
    for item in templist:
        sym = str(item[0])
        if sym not in symbols:
            symbols.append(sym)


    for symbol in symbols:
        print("1111",symbol)
        # symbol = "US500"
        q = f'SELECT timeframe, buyAllowed, sellAllowed FROM fri_trade.active_symbols where symbol = "{symbol}"'
        fri_trade_cursor.execute(q)

        db_output = fri_trade_cursor.fetchall()
        data_to_put = add_buttons_to_db_output(db_output, symbol)


        with use_scope("result", clear=True) as scope_name:
            put_buttons([dict(label='Refresh', value='xxx')], onclick=[main, ])
            # put_table([
            #     ['TIMEFRAME', "BUY allowed", "SELL allowed"],
            #     *data_to_put,
            #     ],
            #     header=[span(symbol, col=3)])


            with use_scope("second", clear=True) as scope_name2:
                put_tabs([
                    {'title': symbol, 'content': put_table([
                        ['TIMEFRAME', "BUY allowed", "SELL allowed"],
                        *data_to_put,
                        ],
                        header=[span(symbol, col=3)])},
                    {'title': "I'm leaving", 'content': None}
                ])





        # tpl = '''
        #         <details {{#open}}open{{/open}}>
        #             <summary>{{title}}</summary>
        #             {{#contents}}
        #                 {{& pywebio_output_parse}}
        #             {{/contents}}
        #         </details>
        #         '''
        #
        # put_widget(tpl, {
        #     "open": True,
        #     "title": 'More content',
        #     "contents": [
        #         'text',
        #         put_markdown('~~Strikethrough~~'),
        #         put_table([
        #             ['Commodity', 'Price'],
        #             ['Apple', '5.5'],
        #             ['Banana', '7'],
        #         ])
        #     ]
        # })



    # def row_action(choice, id):
    #     put_text("You click %s button with id: %s" % (choice, id))
    #
    # put_buttons(['edit', 'delete'], onclick=partial(row_action, id=1))
    #

    # def edit():
    #     put_text("You click edit button")
    # def delete():
    #     put_text("You click delete button")
    #
    # put_buttons(['edit', 'delete'], onclick=[edit, delete])


    # put_table([
    #     ['Type', 'Content'],
    #     ['html', put_html('X<sup>2</sup>')],
    #     ['text', '<hr/>'],
    #     ('buttons', put_buttons(['A', 'B'], onclick=...)),  # ..doc-only
    #     ['buttons', put_buttons(['A', 'B'], onclick=put_text)],  # ..demo-only
    #     ['markdown', put_markdown('`Awesome PyWebIO!`')],
    #     ['file', put_file('hello.text', b'hello world')],
    #     ['table', put_table([['A', 'B'], ['C', 'D']])]
    # ])

if __name__ == '__main__':
    start_server(main, host="localhost", port=9011)
