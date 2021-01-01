import email_utils
import data_handling
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Process price data for tickers either from a (-f) text file or from a given list of tickers.')
    parser.add_argument('tickers', metavar='T', type=str, nargs='*', help='List tickers to analyze, not necessary if providing file, or a  proper .tickers.txt exists')
    parser.add_argument('-f', dest='file', help='file already containing tickers, if more tickers are given, new tickers will be written to this file')
    parser.add_argument('-e', dest='email', required=True, help='Email to send information to and from, will require approving credentials.')
    args = parser.parse_args()
    
    tickers_file = '.tickers.txt' # default file, if not found raises error
    if args.file:
        tickers_file = args.file
    if args.tickers:
        with open(tickers_file, 'w+') as f:
            f.writelines(args.tickers)
     
    if is_email_address(args.email):
        email_address = args.email
    else:
        raise ValueError("Not a valid email address.")

    # break down content of get_all_info into this main
    responses, img_filename = data_handling.gen_all_info(tickers_file)

    if len(responses) < 1:
        content = "no relevant info to report"
    else:
        content = make_email_text_content(responses)

    email_service = email_utils.load_credentials_build_service()

    email_encoded = email_utils.create_email(email_address, email_address,
                                            'SMA Crossovers', content, img_filename)
    email_utils.send_email(email_service, email_encoded, email_address)


def make_email_text_content(responses):
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
        return '@' in arg and \
                '.' in arg and \
                arg.index('@') > 0 and \
                arg.index('.') < len(arg) - 1 \
                and arg.index('.') - arg.index('@') > 1

if __name__ == '__main__':
    main()

