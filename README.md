# histhb: history to homebank

histb is a script to convert several bank account history formats to a CSV file importable to HomeBank (http://homebank.free.fr/).

## Supported banks and how to get the history file

### Česká spořitelna (Czech Republic)
1. login to Servis24
2. go to account history
3. select a timeframe
4. scroll down, choose 'CSV with semicolon as delimiter', download

### Komerční banka (Czech Republic)
1. login to internetbanking
2. go to account history
3. select a timeframe
4. download the CSV version

### ERA (Czech Republic)


## Usage examples
```
$ ./histhb.py --bank csas --input src/TH_20160601-20160630.csv --output out/csas_201606.csv
```
