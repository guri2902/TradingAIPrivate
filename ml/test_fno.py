from datetime import date
import json
import traceback

from jugaad_data.nse.history import derivatives_raw


print("=" * 70)
print("JUGAAD F&O RAW RESPONSE DIAGNOSTIC")
print("=" * 70)

try:

    data = derivatives_raw(
        symbol="NIFTY",
        from_date=date(2026, 8, 1),
        to_date=date(2026, 8, 17),
        expiry_date=date(2026, 8, 27),
        instrument_type="FUTIDX",
        strike_price=None,
        option_type=None
    )

    print("\nResponse type:")
    print(type(data))

    if isinstance(data, list):

        print("\nNumber of records:")
        print(len(data))

        if len(data) > 0:

            print("\nFirst record:")
            print(
                json.dumps(
                    data[0],
                    indent=2,
                    default=str
                )
            )

            print("\nKeys:")
            print(
                list(data[0].keys())
            )

    elif isinstance(data, dict):

        print("\nDictionary keys:")
        print(list(data.keys()))

        print("\nResponse:")
        print(
            json.dumps(
                data,
                indent=2,
                default=str
            )[:10000]
        )

    else:

        print("\nRaw response:")
        print(data)

except Exception:

    print("\nERROR:")
    traceback.print_exc()