import email_utils
import data_handling
import sys
import argparse

def main():
    tickers_file, email_address = parse_args()

    # break down content of get_all_info into this main
    responses, img_filename = data_handling.gen_all_info(tickers_file)

    if len(responses) < 1:
        print("no relevant info to report")
        sys.exit(0)
    

    content = make_email_text_content(responses)

    email_service = email_utils.load_credentials_build_service()

    email_encoded = email_utils.create_email(email_address, email_address,
                                            'SMA Crossovers', content, img_filename)
    email_utils.send_email(email_service, email_encoded, email_address)


def parse_args():
    """
    parses command line arguments when running this main.py file

    required -e argument must be a valid email address

    -f argument before the name of a text file which contains tickers
    or a list of tickers to run this script on, which will then be saved
    in .tickers.txt file. If '.tickers.txt' exists it will be overwritten
    if only a list of tickers is given
    
    ** using the -f flag and providing a text file of tickers is encouraged
    and takes precedence over any other tickers given
    """
    parser = argparse.ArgumentParser(description='Process price data for tickers either from a (-f) text file or from a given list of tickers.')
    parser.add_argument('tickers', metavar='T', type=str, nargs='*', help='List tickers to analyze, not necessary if providing file, or a  proper .tickers.txt exists')
    parser.add_argument('-f', dest='file', help='file already containing tickers, if more tickers are given, new tickers will be written to this file')
    parser.add_argument('-e', dest='email', required=True, help='Email to send information to and from, will require approving credentials.')
    args = parser.parse_args()
    
    if args.file:
        if not args.file.endswith('.txt'):
            raise ValueError('Given tickers file is not a \'.txt\' file.')
        tickers_file = args.file
    elif args.tickers:
        tickers_file = '.tickers.txt'
        with open(tickers_file, 'w+') as f:
            for ticker in args.tickers:
                f.write(ticker + '\n')
    else:
        raise TypeError('No tickers text file or list of tickers given')
     
    if is_email_address(args.email):
        email_address = args.email
    else:
        raise ValueError("Not a valid email address.")
    
    return tickers_file, email_address

def make_email_text_content(responses):
    """
    parse list of tuples containing tickers and their buy/sell signals
    into the text content for the email to be sent.

    signal values:
    True: BUY
    False: SELL
    None: No strong signal but there is an SMA intersection
    """
    res = ""
    for response in responses:
        ticker, signal = response
        res += ticker + ': SMA convergence points to a possible optimal time to '
        if signal is None:
            res += "No particular BUY or SELL signal"
        elif signal:
            res += 'BUY'
        else:
            res += 'SELL'
        res += '.\n'
    return res

def is_email_address(arg):
    """
    returns True if arg is a valid email, false if not
    """
    return '@' in arg and \
            '.' in arg and \
            arg.index('@') > 0 and \
            arg.index('.') < len(arg) - 1 \
            and arg.index('.') - arg.index('@') > 1

if __name__ == '__main__':
    main()

