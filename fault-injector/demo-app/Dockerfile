# Demo shop app image. The build AND the tests run inside the image, so the
# pipeline behaves the same everywhere (laptop, CI, cloud VM).
FROM maven:3.9-eclipse-temurin-11
WORKDIR /app
COPY pom.xml .
COPY src ./src
# Tests run at image build time: a red test fails the docker build,
# exactly like a CI pipeline going red.
RUN mvn -B test
CMD ["echo", "demo shop app built and tested"]
