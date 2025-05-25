#include <Python.h>
#include <openssl/sha.h>
#include <string.h>

static PyObject* sha256sum(PyObject* self, PyObject* args) {
    Py_buffer buffer;
    if (!PyArg_ParseTuple(args, "y*", &buffer)) {
        return NULL;
    }

    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, buffer.buf, buffer.len);
    SHA256_Final(hash, &sha256);

    char hex[65];
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        sprintf(hex + (i * 2), "%02x", hash[i]);
    }
    hex[64] = 0;

    PyBuffer_Release(&buffer);
    return Py_BuildValue("s", hex);
}

static PyMethodDef ChecksumMethods[] = {
    {"sha256sum", sha256sum, METH_VARARGS, "Compute SHA256 checksum of a buffer"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef checksummodule = {
    PyModuleDef_HEAD_INIT,
    "checksum",
    NULL,
    -1,
    ChecksumMethods
};

PyMODINIT_FUNC PyInit_checksum(void) {
    return PyModule_Create(&checksummodule);
}
