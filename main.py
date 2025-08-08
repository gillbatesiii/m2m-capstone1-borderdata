from dash import Dash, html

app = Dash()

app.layout = html.Div(children="Hello from m2m-capstone1-dash!")
def main():
    print("Hello from m2m-capstone1-dash!")
    app.run(debug=True)


if __name__ == "__main__":
    main()
