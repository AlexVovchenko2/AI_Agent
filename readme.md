# Установка компонентов

### Устанавливаем llama-cpp-python с поддержкой CUDA

```bash
set CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python==0.3.2 --force-reinstall --no-cache-dir
```

### Остальные зависимости

```bash
pip install -r requirements.txt
```