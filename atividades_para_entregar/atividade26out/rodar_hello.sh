# Deve ser rodado dentro do ambiente devenv shell, dentro dessa pasta
# todo add this to the `devenv up` as an option.
echo "Rodar dentro do devenv shell, nesta pasta."
shiny run --reload ./src/app_hello.py
