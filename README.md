# FastAPI with JWT Token-based Authentication

## Want to use this project?

1. Fork/Clone

2. Create and activate a virtual environment:

    ```sh
    $ python3 -m venv venv && source venv/bin/activate
    ```

3. Install the requirements:

    ```sh
    (venv)$ pip install -r requirements.txt
    ```

4. Run the app:

    ```sh
    (venv)$ python main.py
    ```

5. Test at [http://localhost:8081/docs](http://localhost:8081/docs)

Test in client-side using fetch:
```
fetch("http://localhost:8081/user/signup", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    email: "aadarsh@gmail.com",
    password: "aadarsh"
  })
}).then(response => response.json()).then(data => {
    console.log(data);
});
```