
from flask import Flask, request, jsonify, render_template
import pandas as pd
import joblib
import re
import os
from urllib.parse import urlparse


app = Flask(__name__)


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


model = joblib.load(
    os.path.join(
        BASE_DIR,
        "url_phishing_model.pkl"
    )
)


feature_names = joblib.load(
    os.path.join(
        BASE_DIR,
        "url_model_features.pkl"
    )
)


def extract_url_features(url):

    parse_url = url

    if not re.match(
        r"^[a-zA-Z][a-zA-Z0-9+.-]*://",
        parse_url
    ):
        parse_url = "http://" + parse_url

    parsed = urlparse(parse_url)

    hostname = parsed.hostname or ""
    path = parsed.path or ""
    full_url = url


    def digit_ratio(text):

        if not text:
            return 0.0

        return (
            sum(c.isdigit() for c in text)
            / len(text)
        )


    def contains_ip(host):

        return int(
            bool(
                re.match(
                    r"^(?:\d{1,3}\.){3}\d{1,3}$",
                    host
                )
            )
        )


    values = {

        "length_url":
            len(full_url),

        "length_hostname":
            len(hostname),

        "ip":
            contains_ip(hostname),

        "nb_dots":
            full_url.count("."),

        "nb_hyphens":
            full_url.count("-"),

        "nb_at":
            full_url.count("@"),

        "nb_qm":
            full_url.count("?"),

        "nb_and":
            full_url.count("&"),

        "nb_eq":
            full_url.count("="),

        "nb_underscore":
            full_url.count("_"),

        "nb_tilde":
            full_url.count("~"),

        "nb_percent":
            full_url.count("%"),

        "nb_slash":
            full_url.count("/"),

        "nb_star":
            full_url.count("*"),

        "nb_colon":
            full_url.count(":"),

        "nb_comma":
            full_url.count(","),

        "nb_semicolumn":
            full_url.count(";"),

        "nb_dollar":
            full_url.count("$"),

        "nb_space":
            full_url.count(" "),

        "nb_www":
            full_url.lower().count("www"),

        "nb_com":
            full_url.lower().count(".com"),

        "nb_dslash":
            full_url.count("//"),

        "http_in_path":
            int(
                "http" in path.lower()
            ),

        "https_token":
            int(
                "https" in hostname.lower()
            ),

        "ratio_digits_url":
            digit_ratio(full_url),

        "ratio_digits_host":
            digit_ratio(hostname),

        "punycode":
            int(
                "xn--" in hostname.lower()
            ),

        "port":
            int(
                parsed.port is not None
            ),

        "tld_in_path":
            int(
                bool(
                    re.search(
                        r"\.(com|org|net|edu|gov|io|co)(/|$)",
                        path.lower()
                    )
                )
            ),

        "tld_in_subdomain":
            int(
                bool(
                    re.search(
                        r"\.(com|org|net|edu|gov|io|co)\.",
                        hostname.lower()
                    )
                )
            ),

        "abnormal_subdomain":
            int(
                hostname.count(".") >= 3
            ),

        "nb_subdomains":
            max(
                hostname.count(".") - 1,
                0
            ),

        "prefix_suffix":
            int(
                "-" in hostname
            )
    }


    return {
        feature: values[feature]
        for feature in feature_names
    }


@app.route("/")
def home():

    return render_template(
        "index.html"
    )


@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    try:

        data = request.get_json()

        if not data or not data.get("url"):

            return jsonify({
                "error":
                "Please enter a website URL."
            }), 400


        url = data["url"].strip()


        features = extract_url_features(
            url
        )


        input_df = pd.DataFrame(
            [features]
        ).reindex(
            columns=feature_names
        )


        prediction = int(
            model.predict(
                input_df
            )[0]
        )


        probability = model.predict_proba(
            input_df
        )[0]


        # Important indicators
        indicators = []


        if features.get(
            "length_url",
            0
        ) > 75:

            indicators.append(
                "Long URL detected"
            )


        if features.get(
            "ip",
            0
        ) == 1:

            indicators.append(
                "IP address used as hostname"
            )


        if features.get(
            "nb_at",
            0
        ) > 0:

            indicators.append(
                "@ symbol detected"
            )


        if features.get(
            "nb_subdomains",
            0
        ) >= 2:

            indicators.append(
                "Multiple subdomains detected"
            )


        if features.get(
            "ratio_digits_url",
            0
        ) > 0.15:

            indicators.append(
                "High digit ratio"
            )


        if features.get(
            "prefix_suffix",
            0
        ) == 1:

            indicators.append(
                "Hyphen detected in hostname"
            )


        if not indicators:

            indicators.append(
                "No major URL-structure warning "
                "was triggered by the basic checks"
            )


        return jsonify({

            "url":
                url,

            "prediction":
                "Phishing"
                if prediction == 1
                else "Legitimate",

            "legitimate_probability":
                round(
                    float(
                        probability[0]
                    ) * 100,
                    2
                ),

            "phishing_probability":
                round(
                    float(
                        probability[1]
                    ) * 100,
                    2
                ),

            "indicators":
                indicators,

            "features":
                features
        })


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
