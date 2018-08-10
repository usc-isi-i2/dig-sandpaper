from .execute.executor import Executor
from .generate.generator import Generator
from .parameterize.parameterizer import Parameterizer
from .preprocess.preprocessor import Preprocessor
from .postprocess.postprocessor import PostProcessor


class CoarseEngine(object):

    def __init__(self, config):
        self.config = config
        self._initialize()

    def _initialize(self):
        self.preprocessor = Preprocessor(self.config.get("preprocess", {}))
        self.parameterizer = Parameterizer(self.config.get("parameterize", {}))
        self.generator = Generator(self.config.get("generate", {}))
        self.executor = Executor(self.config.get("execute", {}))
        self.postprocessor = PostProcessor(self.config.get("postprocess", {}))

    def generate(self, query):
        # preprocess
        preprocessed_query = self.preprocessor.preprocess(query)
        # parameterize
        parameterized_queries = self.parameterizer. \
            parameterize(preprocessed_query)
        # generate
        generated_queries = [self.generator.generate(q)
                             for q in parameterized_queries]

        return generated_queries

    def execute(self, query):
        generated_queries = self.generate(query)
        # execute
        results = [self.executor.execute(q) for q in generated_queries]

        # postprocess
        postprocessed_results = []
        for q, r in zip(generated_queries, results):
            postprocessed_results.append(self.postprocessor.postprocess(q, self.coarse_results_to_dict(r)))

        return generated_queries, postprocessed_results

    def teardown(self):
        self.executor.teardown()

    @staticmethod
    def coarse_results_to_dict(r):
        if isinstance(r, list):
            return [rr.to_dict() for rr in r]
        else:
            return r.to_dict()
