import requests
import xmltodict
import json
import argparse

class WildfireAPI():

    def __init__(self):
        # We need to get the values to use for our query
        parser = argparse.ArgumentParser(description='Submit a file to WildFire or Query a known hash of a file')
        parser.add_argument('-a', '--action', help='Action to perform, lookup or submit then lookup',
                            choices=['lookup', 'submit'])
        parser.add_argument('-m', '--md5sum', help='If doing a lookup provide the md5 hash of the filel')
        parser.add_argument('-f', '--file', help='the filename to use if doing a submit')
        parser.add_argument('-k', '--key', help='the api key to use to query the wildfire API')
        parser.add_argument('-d', '--debug', help='set to 1 to debug values set', choices=['1', '0'])
        args_namespace = parser.parse_args()
        # take the values of the namespace from argparse and put into a dictionary
        args = vars(args_namespace)

        # Test if variables were passed, if not assign default values
        self.argument_dict = {}
        if args['key']:
            self.argument_dict['key'] = args['key']
        else:
            self.argument_dict['key'] = 'no-key-passed'
        if args['file']:
            self.argument_dict['file'] = args['file']
        else:
            self.argument_dict['file'] = 'test_pdf.pdf'
        if args['md5sum']:
            self.argument_dict['hash'] = args['md5sum']
        else:
            self.argument_dict['hash'] = 'b60a8d7389cb4ee114146aa9f4768b28'
        if args['debug']:
            self.argument_dict['debug'] = args['debug']
        else:
            self.argument_dict['debug'] = '0'
        if args['action']:
            self.argument_dict['action'] = args['action']
        # we default to just doing a lookup on a hash
        else:
            self.argument_dict['action'] = 'lookup'
        # Report URLs are fairly static
        self.argument_dict['report_url'] = 'https://wildfire.paloaltonetworks.com/publicapi/get/report'
        self.argument_dict['submission_url'] = 'https://wildfire.paloaltonetworks.com/publicapi/submit/file'

        # test if debug output needs to be printed out
        self.debugOutput()


    def debugOutput(self):
        '''
        print out debug info if debug enabled
        :return:
        '''
        if self.argument_dict['debug'] == '1':
            for k, v in self.argument_dict.items():
                print('{key} : {value}'.format(key=k, value=v))


    def printResults(self, results=None):
        '''
        prints out the results in a decent format
        :param results: the results of the lookup passed to us
        :return:
        '''
        if results:
            print('{output}\n\n'.format(output=json.dumps(results, indent=1)))
            # this just prints out a subset of the wildfire output
            #print(json.dumps(results['wildfire']['file_info'], indent=1))
        else:
            print('No results from the hash lookup to WildFire API')

    def getReport(self):
        '''
        This will query the WildFire API against a hash provided to get results
        :return: results - a dictionary of the file lookup result
        '''
        # post to the API with the hash to get the results
        post_data = {'apikey': self.argument_dict['key'], 'format': 'xml', 'hash': self.argument_dict['hash']}
        r = requests.post(self.argument_dict['report_url'], data=post_data)

        try:
            # convert xml to dictionary and return
            results = xmltodict.parse(r.text)
            return results
        except Exception as e:
            print(e)

    def submitFile(self):
        '''
        This will submit a file for WildFire evaluation and return a hash
        :return: file_info - file_info contains lots of info including the hash
        '''
        # Try to open the file to submit
        with open(self.argument_dict['file'], 'rb') as f:
            # post to the API with the file and include the filename in the data posted as well
            post_data = {'apikey': self.argument_dict['key'], 'file': '{filename}'.format(
                filename=self.argument_dict['file'])}
            r = requests.post(self.argument_dict['submission_url'], data=post_data, files={'file': f})

            try:
                file_info = xmltodict.parse(r.text)

                # Return the file info and the hash as well
                return file_info
            except Exception as e:
                print(e)

    def doWork(self):
        '''
        This will look at the action and do the proper things
        :return:
        '''
        if self.argument_dict['action'] == 'submit':
            # first we need to submit the file, and get the file hash of that file
            file_info = self.submitFile()
            print(json.dumps(file_info, indent=1))
            # pull out just the file_hash to use for calling the lookup service
            file_hash = file_info['wildfire']['upload-file-info']['md5']
            # we override the hash in argument_dict to the new file hash
            self.argument_dict['hash'] = file_hash

            # Now call the lookup service
            results = self.getReport()
            # pass results to function to print them out
            self.printResults(results)

        if self.argument_dict['action'] == 'lookup':
            # perform a lookup based on the hash
            results = self.getReport()
            # pass results to function to print them out
            self.printResults(results)




test = WildfireAPI()
test.doWork()

