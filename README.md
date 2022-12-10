# BC-experiment-simulator
ブロックチェーンを利用した貸借取引実証実験のロジックのシミュレーションを行う。

## Financial data
株価データは [pandas-datareader](https://github.com/pydata/pandas-datareader) を利用して Yahoo! Finance から取得。
### 追記@2021-07-07
現在 `pandas-datareader` は Yahoo! Finance の API アクセス制限？によってアクセスが正常にできない様子。
代わりに[yfinance](https://github.com/ranaroussi/yfinance) を利用してデータを取得。

## Usage
Refer to notebooks in  `/sandbox`.

### ~~シナリオ②（JCT 可変複数裏付け）~~
`VariableLocalTransaction()`クラスを利用して取引を再現。

[`sandbox/simulate_VariableLocal.ipynb`](https://github.com/maru919/BC-experiment-simulator/blob/master/sandbox/simulate_VariableLocal.ipynb) を参照。

### ~~シナリオ③（JCT 固定複数裏付け）~~
`StableTransaction()`クラスを利用して取引を再現。

[`sandbox/simulate_Stable.ipynb`](https://github.com/maru919/BC-experiment-simulator/blob/master/sandbox/simulate_Stable.ipynb) を参照。

### 実証実験用シミュレータ
`/scripts/variable_local.py`　の `AutoAdjustmentTransaction()` で実装。
[`sandbox/simulate_AutoAdjustment`]() を参照。

## Sandbox
検証・シミュレーション用の .ipynb ファイルなどは `sandbox` 以下に配置。
