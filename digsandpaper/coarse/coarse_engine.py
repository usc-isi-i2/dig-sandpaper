from execute.executor import Executor
from generate.generator import Generator
from parameterize.parameterizer import Parameterizer
from preprocess.preprocessor import Preprocessor


class CoarseEngine(object):

    def __init__(self, config, host, port):
        self.config = config
        self._initialize()

    def _initialize(self):
        self.preprocessor = Preprocessor(self.config.get("preprocess", {}))
        self.parameterizer = Parameterizer(self.config.get("parameterize", {}))
        self.generator = Generator(self.config.get("generate", {}))
        self.executor = Executor(self.config.get("execute", {}))

    def execute(self, query):
        # preprocess
        preprocessed_query = self.preprocessor.preprocess(query)
        # parameterize
        parameterized_queries = self.parameterizer.\
            parameterize(preprocessed_query)
        # generate
        generated_queries =[self.generator.generate(q) for q in parameterized_queries]
        # execute
        results = [self.executor.execute(q) for q in generated_queries]

        return (generated_queries, results)
