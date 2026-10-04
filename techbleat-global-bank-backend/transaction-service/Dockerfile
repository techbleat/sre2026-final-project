FROM maven:3.9.8-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre
WORKDIR /app
RUN useradd -m -u 1001 app && chown app:app /app
COPY --from=build /app/target/transaction-service-1.0.0.jar app.jar
RUN chown app:app /app/app.jar
USER app
ENTRYPOINT ["java", "-jar", "app.jar"]
