import os
import shutil
import tempfile

from digital_twin_distiller.text_readers import JsonReader, TextReader
from digital_twin_distiller.text_writers import JsonWriter


class DataSnapshot:
    """
    The goal of this task is to save a snapshot from the current status of the input files into a compressed archive
    of the JSONS, where the Project structure's data dictionary is represented by a single JSON.

    Arbitrary pre-processing steps can be defined and added to the project.

    The pre-processed files of the input are saved into a single archive.

    The default compression methodology is the gzip, other supported file formats are: bz2, lzma and the zipfile.
    """

    # list of the arbitrary preprocessing steps
    preprocessors = []
    # a temporary directory to store the data for a parallelized
    tmp_directory = []

    def __init__(self, input_stack):
        # the snapshot inherits the input stack from the main Project
        self.input_list = input_stack

    # TODO: parhuzamosított mukodes esetén az alapegység számunkra nem a sor lesz, hanem a dokumentum, annak is a nyers
    #       szovege. Ezt azért tehetjük meg, mert
    # for pre_p in self.preprocessors:
    #    for inp_data in self.input_list:
    #        pre_p.run(inp_data)

    @staticmethod
    def save(input_stack: list, file_path):
        """
        This function simply saves the dictionaries of the input stack into a separate json.

        The function is looking for a 'FileName' tag in the input json, then tries to save it under this name, if this
        field is missing, it saves under a template name, generated by the next method of the template directory.

        :param input_stack: is a list of dictionaries
        :param file_path: the name and the path of the produced output file with extension, if the extension is
        not defined or not supported the file is comprassed into a single tar.gz.
        """

        with tempfile.TemporaryDirectory() as tmpdirname:
            for data in input_stack:
                if data.get("FileName"):
                    JsonWriter().write(data, os.path.join(tmpdirname, data.get("FileName") + ".json"))
                else:
                    tmp = next(tempfile._get_candidate_names())
                    JsonWriter().write(data, os.path.join(tmpdirname, tmp + ".json"))
            shutil.make_archive(file_path, "zip", tmpdirname)
        return

    @staticmethod
    def load_stack(archive_path):
        """This function simply uncomprass a zipped file of jsons and gives back its content in a list if dicts, which
        can be update or load the input_stack of a
        """

        stack = []

        with tempfile.TemporaryDirectory() as tmpdirname:
            shutil.unpack_archive(archive_path, tmpdirname)
            # print(os.listdir(tmpdirname))
            for file in os.listdir(tmpdirname):
                try:
                    tmp = JsonReader().read(os.path.join(tmpdirname, file))
                except Exception:
                    tmp = TextReader().read(os.path.join(tmpdirname, file))
                stack.append(tmp)
        return stack