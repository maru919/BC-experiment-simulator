# BC-experiment-simulator
[日証金](https://www.taisyaku.jp/)との共同研究で行っているブロックチェーン実証実験のロジックのシミュレーションを行う。

## Financial data
株価データは [pandas-datareader](https://github.com/pydata/pandas-datareader) を利用して Yahoo! Finance から取得。
### 追記@2021-07-07
現在 `pandas-datareader` は Yahoo! Finance の API 制限？によってアクセスが正常にできない様子。
代わりに、[yfinance](https://github.com/ranaroussi/yfinance) を利用してデータを取得。

## Usage
coming soon.

## sandBox
検証用の .ipynb ファイルなどは `sandbox` 以下に配置。
