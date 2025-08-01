import uvicorn
from pydantic import BaseModel

from wiederverwendbar.fastapi import FastAPI
from wiederverwendbar.pydantic import Version


class Sample(BaseModel):
    version: Version


app = FastAPI()

@app.get("/version")
def get_sample() -> Sample:
    version = Version(major=1, minor=0, patch=0)
    return Sample(version=version)

@app.post("/version")
def post_sample(sample: Sample) -> Sample:
    # Here you can process the sample as needed
    return sample


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    version_major = 0
    version_minor = 1
    version_patch = 0
    version_str = f"{version_major}.{version_minor}.{version_patch}"
    version = Version(major=version_major,
                      minor=version_minor,
                      patch=version_patch)

    sample1 = Sample(version=version)
    sample1.version.major = 34
    print(sample1.model_dump_json(indent=2))

    sample2 = Sample(version=version_str)
    print(sample2.model_dump_json(indent=2))

    print()
